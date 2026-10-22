# deploy/: Ko'z on AWS (ap-southeast-2, Sydney)

The click list is `docs/AWS_DAY.md`. What runs where:

    Mac:  camera -> OpenCV 5 (privacy guard, face blur, blocks) -> runner --cloud wss://IP/v1/runner
                                  │ outbound WebSocket, contract JSON only (no frames)
    AWS:  Nginx (HTTPS, Let's Encrypt IP certificate) -> web app (Node, 127.0.0.1:4173) -> DynamoDB
          Bedrock (Amazon Nova 2 Lite, EU Regions) <- the planner on the Mac (only the typed sentence)

| File | What it is |
|---|---|
| `koz-aws.json` | CloudFormation: DynamoDB table `koz-web` (TTL on `expires_at`), security group (80 and 443 only, no SSH), launch template (IMDSv2, encrypted 8 GiB gp3), t3.micro Ubuntu 24.04, Elastic IP, a generated owner password in Secrets Manager. |
| `iam-server-role-policy.json` | The server's role `koz-web-ec2`, made once in the IAM console (EC2 use case, so only EC2 can use it; plus `AmazonSSMManagedInstanceCore`): only the `koz-web` table and the owner password. The stack makes no IAM (security review, Oct 20). |
| `iam-deployer-policy.json` | What Claude's AWS CLI user `koz-deployer` may do: the stack `koz` and its resources in Sydney, one t3.micro and that one role only through CloudFormation, no shell on the server. Denied: any IAM change, reading the owner password, anything outside ap-southeast-2. Islombek removes it after the deploy. |
| `install.sh` | First boot: Node.js 22 (checksum checked), Nginx, Certbot 5.4+, builds `web/`, the `koz-web` service, then the IP certificate (staging test first) with automatic renewal. Log: `/var/log/koz-install.log`. |
| `nginx-http.conf`, `nginx-https.conf` | Before and after the certificate: WebSocket for `/v1/runner`, unbuffered `/api/events`, no access logs. |
| `koz-web.service` | The web app as user `koz`, read-only system, writable only `/var/lib/koz`. |

Not tested on AWS yet (no AWS actions before Oct 19); `tests/test_deploy.py` checks the files' safety
properties, and the runner's cloud link was tested against the web app's token mode on this computer.
