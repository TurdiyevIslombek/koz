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
    """Islombek makes the role once in the IAM console (EC2 use case: trusted by EC2 only) with this
    policy; the stack makes no IAM at all, so the deployer needs no right to make roles (Oct 20)."""
    assert not any(r["Type"].startswith("AWS::IAM::") for r in RES.values())
    assert RES["Instance"]["Properties"]["IamInstanceProfile"] == {"Ref": "ServerInstanceProfile"}
    statements = json.loads((DEPLOY / "iam-server-role-policy.json").read_text())["Statement"]
    actions = [a for s in statements for a in s["Action"]]
    # exactly what web/server/dynamo.mjs calls (a TransactWriteItems of Puts needs PutItem; "TransactWriteItems"
    # itself is not an IAM action: the IAM console rejected it, Oct 21)
    assert actions == ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:Query",
                       "secretsmanager:GetSecretValue"]
    used = set(re.findall(r"\b(GetItem|PutItem|DeleteItem|Query|UpdateItem|BatchGetItem|BatchWriteItem|Scan)Command\b",
                          (DEPLOY.parent / "web/server/dynamo.mjs").read_text()))
    assert {"dynamodb:" + u for u in used} <= set(actions)
    assert [r for s in statements for r in s["Resource"]] == [   # exactly that secret (+ AWS's 6 random characters)
        "arn:aws:dynamodb:ap-southeast-2:*:table/koz-web", "arn:aws:secretsmanager:ap-southeast-2:*:secret:koz-owner-password-??????"]
    assert RES["OwnerPassword"]["Properties"]["Name"] == "koz-owner-password"


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


def test_the_deployer_policy_is_sydney_only_and_cannot_read_the_password():
    """deploy/iam-deployer-policy.json: what Claude's AWS CLI user may do (Oct 20). Islombek creates
    it in the console; root credentials are never used."""
    text = (DEPLOY / "iam-deployer-policy.json").read_text()
    assert len(re.sub(r"\s", "", text)) <= 6144                      # fits a customer managed policy
    statements = json.loads(text)["Statement"]
    allows = [s for s in statements if s["Effect"] == "Allow"]
    for s in allows:
        actions = [s["Action"]] if isinstance(s["Action"], str) else s["Action"]
        assert "*" not in actions and not any(a.endswith(":*") and a != "dynamodb:*" for a in actions)
        assert not any(a.startswith("secretsmanager:GetSecretValue") for a in actions)
    deny = {s["Sid"]: s for s in statements if s["Effect"] == "Deny"}
    assert deny["NeverReadTheOwnerPassword"]["Action"] == "secretsmanager:GetSecretValue"
    region = deny["NothingOutsideSydney"]
    assert region["Condition"] == {"StringNotEquals": {"aws:RequestedRegion": "ap-southeast-2"}}
    assert set(region["NotAction"]) == {"iam:*", "sts:*", "signin:*", "freetier:*", "budgets:*"}   # global services only
    run = [s for s in allows if s["Action"] == "ec2:RunInstances" and s["Resource"] == "arn:aws:ec2:ap-southeast-2:*:instance/*"]
    assert run[0]["Condition"]["StringEquals"] == {"ec2:InstanceType": "t3.micro"}
    # IAM: pass the one server role to EC2 and read it; nothing that makes or changes IAM (review, Oct 20)
    iam = [a for s in allows for a in ([s["Action"]] if isinstance(s["Action"], str) else s["Action"]) if a.startswith("iam:")]
    assert all(a == "iam:PassRole" or a.startswith(("iam:Get", "iam:List")) for a in iam)
    assert {"iam:Create*", "iam:Put*", "iam:Attach*", "iam:Update*"} <= set(deny["NoIamChanges"]["Action"])
    passing = next(s for s in allows if s["Action"] == "iam:PassRole")
    assert passing["Resource"].endswith("role/koz-web-ec2") and passing["Condition"]["StringEquals"]["iam:PassedToService"] == "ec2.amazonaws.com"
    # stopping a server: only the stack's own, by CloudFormation's aws: tag, which nobody can set by hand
    stop = next(s for s in allows if s["Sid"] == "StopOnlyThatServer")
    assert list(stop["Condition"]["StringEquals"]) == ["aws:ResourceTag/aws:cloudformation:stack-name"]
    # no shell on the server (root there can read the password file), no console output (review, Oct 21)
    every = [a for s in allows for a in ([s["Action"]] if isinstance(s["Action"], str) else s["Action"])]
    assert not any(a.startswith(("ssm:SendCommand", "ssm:StartSession", "ec2:GetConsoleOutput", "ec2-instance-connect:")) for a in every)
    # a server, and the server role, only through CloudFormation: no hand-made server with the role
    via = {"ForAnyValue:StringEquals": {"aws:CalledVia": ["cloudformation.amazonaws.com"]}}
    for s in allows:
        if s["Action"] in ("ec2:RunInstances", "iam:PassRole"):
            assert s["Condition"]["ForAnyValue:StringEquals"] == via["ForAnyValue:StringEquals"], s["Sid"]
    assert next(s for s in allows if s["Sid"] == "OwnerPasswordSecretButNotItsValue")["Resource"].endswith("secret:koz-owner-password-*")


def test_security_group_texts_use_only_what_ec2_accepts():
    """EC2 refused the first stack (Oct 21): an apostrophe in "Ko'z" is not allowed in a security group
    or rule description (a-zA-Z0-9. _-:/()#,@[]+=&;{}!$* only, under 256 characters)."""
    allowed = re.compile(r"^[a-zA-Z0-9. _\-:/()#,@\[\]+=&;{}!$*]{0,255}$")
    sg = RES["SecurityGroup"]["Properties"]
    for text in [sg["GroupDescription"]] + [r["Description"] for r in sg["SecurityGroupIngress"]]:
        assert allowed.match(text), text
