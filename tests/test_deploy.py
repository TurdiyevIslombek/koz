"""The AWS deployment files (deploy/): checked here because CloudFormation and Nginx can't run on
this computer. These pin the properties that matter: least privilege, no SSH, encrypted disk,
IMDSv2, the table's auto-delete, HTTPS done right, and no password in user data or logs."""
import json
import re
import subprocess
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent.parent / "deploy"
TEMPLATE = json.loads((DEPLOY / "koz-aws.json").read_text())
RES = TEMPLATE["Resources"]


def test_only_https_and_the_certificate_check_are_open():
    rules = RES["SecurityGroup"]["Properties"]["SecurityGroupIngress"]
    assert sorted((r["FromPort"], r["ToPort"]) for r in rules) == [(80, 80), (443, 443)]   # no 22, 4173, 8765


def test_the_server_is_small_encrypted_and_uses_imdsv2():
    instance = RES["Instance"]["Properties"]
    assert instance["InstanceType"] == "t3.micro" and instance["CreditSpecification"] == {"CPUCredits": "standard"}
    data = RES["LaunchTemplate"]["Properties"]["LaunchTemplateData"]
    assert data["MetadataOptions"]["HttpTokens"] == "required"
    disk = data["BlockDeviceMappings"][0]["Ebs"]
    assert disk == {"VolumeSize": 8, "VolumeType": "gp3", "Encrypted": True, "DeleteOnTermination": True}
    assert "KeyName" not in instance   # no SSH key: Session Manager only


def test_the_table_deletes_old_rows_by_itself():
    table = RES["Table"]["Properties"]
    assert table["TimeToLiveSpecification"] == {"AttributeName": "expires_at", "Enabled": True}   # contract 12
    assert table["ProvisionedThroughput"] == {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
    assert "PointInTimeRecoverySpecification" not in table and "StreamSpecification" not in table


def test_the_server_role_can_touch_only_its_table_and_its_password():
    statements = RES["Role"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
    actions = [a for s in statements for a in s["Action"]]
    assert all("*" not in a for a in actions)
    assert {json.dumps(r) for s in statements for r in s["Resource"]} == {
        json.dumps({"Fn::GetAtt": ["Table", "Arn"]}), json.dumps({"Ref": "OwnerPassword"})}
    assert RES["Role"]["Properties"]["ManagedPolicyArns"] == ["arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"]


def test_the_password_is_made_by_aws_and_never_in_user_data():
    assert RES["OwnerPassword"]["Properties"]["GenerateSecretString"]["PasswordLength"] >= 20
    user_data = RES["Instance"]["Properties"]["UserData"]["Fn::Base64"]["Fn::Sub"]
    assert "Password" not in user_data.replace("${OwnerPassword}", "") and "install.sh" in user_data
    assert "OwnerPassword" not in json.dumps(TEMPLATE["Parameters"])   # nothing typed in the console


def test_the_server_waits_for_its_fixed_ip_before_downloading():
    user_data = RES["Instance"]["Properties"]["UserData"]["Fn::Base64"]["Fn::Sub"]
    assert user_data.index("meta-data/public-ipv4") < user_data.index("apt-get") < user_data.index("git clone")
    braces = [m for m in re.findall(r"\$\{([^}]*)\}", user_data)]
    assert set(braces) <= {"RepoRef", "RepoUrl", "ElasticIp", "OwnerPassword", "AWS::Region", "Table", "CertEmail"}


def test_installer_syntax_and_its_safety_steps():
    assert subprocess.run(["bash", "-n", str(DEPLOY / "install.sh")]).returncode == 0
    script = (DEPLOY / "install.sh").read_text()
    assert "sha256sum -c" in script                                   # Node.js build checked
    assert "--preferred-profile shortlived" in script and "--ip-address" in script
    assert script.index('certbot "${CERT[@]}" --dry-run') < script.index('certbot "${CERT[@]}"                      #')
    assert "certbot renew --dry-run" in script
    assert not re.search(r"echo[^\n]*PASSWORD", script)              # the password is never printed
    assert "chmod 0640 /etc/koz/env" in script and "unset PASSWORD" in script


def test_nginx_keeps_the_app_private_and_streams_events_unbuffered():
    https = (DEPLOY / "nginx-https.conf").read_text()
    assert https.count("proxy_pass http://127.0.0.1:4173;") == 3
    runner = https[https.index("location = /v1/runner"):https.index("location /api/events")]
    assert "proxy_set_header Upgrade $http_upgrade;" in runner and "Authorization $http_authorization" in runner
    events = https[https.index("location /api/events"):]
    assert "proxy_buffering off;" in events
    assert "listen 443 ssl http2" in https and "http2 on;" not in https   # Nginx 1.24 on Ubuntu 24.04
    assert "access_log off;" in https
    service = (DEPLOY / "koz-web.service").read_text()
    assert "User=koz" in service and "ProtectSystem=strict" in service and "NoNewPrivileges=true" in service
