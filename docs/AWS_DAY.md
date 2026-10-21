# AWS day: who does what

New plan (Oct 20): **you** do the console and Terminal steps marked **You**; **Claude** runs the AWS
CLI as a limited user, `koz-deployer`, and shows you every command that creates or changes something
before running it. Claude never uses root credentials, never sees a key or a password, and works only
in **Europe (Frankfurt) eu-central-1**. If the console ever asks you to upgrade the account or to pay
for something: **stop** and tell Claude.

Done so far: the $1 budget (step 1, Oct 19). The AWS CLI 2.38.3 is installed on the Mac (Claude,
Oct 20; default region eu-central-1).

Copying a file to paste in the console: in Terminal, in the project folder, the `pbcopy` line puts
the file in the clipboard; then click in the console's box, select all (Cmd+A) and paste (Cmd+V).
```bash
cd ~/AI/competitions/opencv-flybrain
```

## Part A. You, in the console (about 15 minutes)

**A1. Region.** Top right of the console, the region name → **Europe (Frankfurt) eu-central-1**.
(It was on Sydney, ap-southeast-2, when you copied the agent-toolkit text: switch it.)

**A2. The server's role** (what the server may do: only its table and its password).
```bash
pbcopy < deploy/iam-server-role-policy.json
```
1. Console search bar: type **IAM** → open **IAM**.
2. Left menu **Roles** → **Create role**.
3. **Trusted entity type**: **AWS service**. **Service or use case**: **EC2**. **Use case**: **EC2**
   (the first one) → **Next**.
4. In the search box type `AmazonSSMManagedInstanceCore` → tick it → **Next**.
5. **Role name**: `koz-web-ec2` → **Create role** (bottom right).
6. In the list of roles, click **koz-web-ec2** → tab **Permissions** → **Add permissions** →
   **Create inline policy**.
7. Click **JSON** → click in the box → Cmd+A → Cmd+V → **Next**.
8. **Policy name**: `koz-web-table-and-password` → **Create policy**.

**A3. The policy for Claude's user** (what Claude may do; it can't change IAM or read your password).
```bash
pbcopy < deploy/iam-deployer-policy.json
```
1. IAM → left menu **Policies** → **Create policy**.
2. Click **JSON** → click in the box → Cmd+A → Cmd+V → **Next**.
3. **Policy name**: `koz-deployer` → **Create policy**.

**A4. Claude's user.**
1. IAM → left menu **Users** → **Create user**.
2. **User name**: `koz-deployer`.
3. Tick **Provide user access to the AWS Management Console**. If it asks who will use it, choose
   **I want to create an IAM user**.
4. **Console password**: **Custom password** → type a new password (keep it to yourself; never in
   chat). Untick **Users must create a new password at next sign-in**. → **Next**.
5. **Permissions options**: **Attach policies directly**. Search `koz-deployer` → tick it. Search
   `SignInLocalDevelopmentAccess` → tick it. → **Next** → **Create user**.
6. The last page shows the **Console sign-in URL** (`https://<numbers>.signin.aws.amazon.com/console`):
   write it down. Don't download the .csv.

**A5. The Bedrock key for the planner** (only the typed sentence goes to Bedrock).
1. Console search: **Amazon Bedrock** → open it (check the region is still Frankfurt).
2. Left menu **API keys** → **Generate long-term API keys** → expiry **30 days** → **Generate**.
3. Copy the key (it is shown once).
4. In Terminal: `open -e .env` (opens the file in TextEdit). Add this line at the end (or replace the
   line if one starts with `AWS_BEARER_TOKEN_BEDROCK=`), paste your key after the `=`, save (Cmd+S),
   close:
   ```
   AWS_BEARER_TOKEN_BEDROCK=
   ```
   (The region is Frankfurt by default; no other line needed.)
5. If Bedrock asks you to request model access for **Nova 2 Lite**: **Model catalog** → **Nova 2 Lite** →
   request access, if a button is shown.

**A6. Log the CLI in as `koz-deployer`** (in Terminal, you type it):
```bash
aws login
```
A browser page opens. Sign in as the **IAM user `koz-deployer`** (account ID or the sign-in URL from
A4, user name `koz-deployer`, your password), **not** with your root email. If it offers to continue
as your root user, choose to sign in with another user instead. Allow the access → Terminal says it
is logged in (for up to 12 hours; run `aws login` again after that).

Then tell Claude **"done"**.

## Part B. Claude (you only say yes or no)

1. Read-only checks: that the CLI is `koz-deployer` and not root (Claude stops if it is root); the
   free plan's state and credits; the $1 budget; the role from A2; the template is valid, Frankfurt
   has its default network, the Ubuntu image is found, t3.micro is free-plan eligible.
2. Claude shows you the exact command that creates the stack `koz` → **you say yes** → Claude runs
   it and watches it (about 5 minutes) and the server's own install (about 10 minutes). If creating
   fails, CloudFormation removes what it made by itself; any other delete, Claude asks first.
   If the link doesn't work after 15 minutes, Claude asks you to read the install log (Claude has no
   shell on the server, on purpose): **EC2** → **Instances** → **koz-web** → **Connect** →
   **Session Manager** → **Connect**, type `sudo tail -50 /var/log/koz-install.log`, and send the
   last lines.
3. Meanwhile, the 20-sentence test with Bedrock (your key from A5). **If either set is under 18/20,
   the rule planner stays the default** and the key line comes out of `.env`.
4. When it's ready: the `https://…` link opens with a valid lock; the judges' view (no login) has no
   camera picture and no eye; the costs stay inside the free plan.
5. **You remove Claude's write rights** (they are needed only for the deploy): IAM → **Users** →
   **koz-deployer** → tab **Permissions** → tick **koz-deployer** → **Remove** → **Remove policy**.

Why step 5: whoever deploys the server writes the script it runs at start, so in principle could make
it reveal the owner password. The policy blocks the direct ways (no reading the secret, no shell on
the server, no server made by hand with its role: only through the `koz` stack), and you approve
every create or change; removing the policy after the deploy closes the rest.

## Part C. You, after Claude says the server is ready

**C1. The owner password.** Console search **Secrets Manager** → the secret named
**koz-owner-password** → **Retrieve secret value** → copy. Open the `https://…` link Claude gives you →
log in with it. Don't paste it anywhere else.

**C2. The runner token.** In the web app: **Create runner token** → **Copy** (shown once; a new one
cancels the old one). In Terminal `open -e .env`, add the line below with the token after `=`, save:
```
KOZ_RUNNER_TOKEN=
```

**C3. Connect the Mac** (Claude gives you the exact address):
```bash
.venv/bin/python -m koz.server --i-own-this-camera --window --cloud wss://THE-IP/v1/runner
```
The web app says the device is connected. Type a job in Setup and watch it.

**C4. Before you give judges the link:** open it in a private window on your phone (mobile data):
it loads with a lock; without logging in you can't start anything; unplugging the Mac's internet shows
"offline", never old numbers as live.

## After judging

CloudFormation → **koz** → **Delete** (server, IP, database and password secret go; save any trial
summaries first). Bedrock → **API keys** → delete the key. IAM → **Users** → delete `koz-deployer`;
**Roles** → delete `koz-web-ec2`; **Policies** → delete `koz-deployer`. Keep the $1 budget. Look at
Billing the next day.

Costs (Codex's estimate, to confirm in the console): the server about $9–10 a month, the fixed IP
$3.65 a month, the disk about $1, the password secret $0.40, the database within the free allowance,
Bedrock a few planner calls (each about 400 words of input). On an active Free plan, credits cover
these; the $1 budget warns you if real money is charged.

## What was done (log)

- Oct 19: $1 budget (Islombek).
- Oct 20–21: AWS CLI 2.38.3 installed with Homebrew (Claude). A security review of Claude's first
  deployer policy found two holes (it could make a role with any powers; a `Name` tag could be put on
  any server); fixed before anything was made: the stack makes no IAM, the server role is made once
  in the console, and the deployer can't change IAM (`tests/test_deploy.py`). A second review found
  the deployer could still reach the password through the server (a shell command on it, or a server
  made by hand with its role): removed the shell and the console output, servers and the role only
  through CloudFormation, the password secret has a fixed name the server role names exactly, and
  the write rights are removed after the deploy (B5).
