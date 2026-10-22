# AWS day: who does what

New plan (Oct 20): **you** do the console and Terminal steps marked **You**; **Claude** runs the AWS
CLI as a limited user, `koz-deployer`, and shows you every command that creates or changes something
before running it. Claude never sees a key or a password, and works only in **Asia Pacific (Sydney)
ap-southeast-2**. If the console ever asks you to upgrade the account or to pay for something:
**stop** and tell Claude.

**Your account is a "new AWS experience" account** (made with Google; Oct 21): it signs in through
**Change to new experience** → your Gmail → Google, it has one project, **Proof of Concept**, and no
region menu: AWS put the project in **Sydney** because the contact address is in Uzbekistan, and it
blocks other regions for servers and databases (only Bedrock's AI calls may go anywhere). Islombek
chose to stay on it (free plan, nothing irreversible) instead of upgrading to get Frankfurt.

Done so far: the $1 budget (Oct 19). The AWS CLI 2.38.3 is installed on the Mac (Claude, Oct 20).

The **console** is the AWS website (console.aws.amazon.com). When a step says "paste the text",
Claude has already copied it for you: click in the box, press Cmd+A, then Cmd+V. (Or copy it yourself
in Terminal, in the project folder: `pbcopy < the-file`.)

## Part A. You, in the console (about 15 minutes)

**A1. Sign in.** console.aws.amazon.com → in the blue box, **Change to new experience** → your Gmail
→ **Continue** → Google. You see **Console Home | Proof of Concept**. There is no region menu: that's
right (Sydney).

**A2. The server's role** (what the server may do: only its table and its password).
Claude copies `deploy/iam-server-role-policy.json` for you.
1. Console search bar at the top: type **IAM** → open **IAM**.
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
Claude copies `deploy/iam-deployer-policy.json` for you.
1. IAM → left menu **Policies** → **Create policy**.
2. Click **JSON** → click in the box → Cmd+A → Cmd+V → **Next**.
3. **Policy name**: `koz-deployer` → **Create policy**.

**A4. Claude's user** (in this kind of account IAM users have no console sign-in: a key only).
1. IAM → left menu **IAM users** → **Create user** → **User name** `koz-deployer` → **Next**.
2. **Attach policies directly** → search `koz-deployer` → tick it → **Next** → **Create user**.
3. Click **koz-deployer** → tab **Security credentials** → **Create access key** → use case
   **Command Line Interface (CLI)** → tick the confirmation → **Next** → **Create access key**.
4. Keep that page open (the secret is shown once). Don't download the .csv. Never paste the key in chat.
5. Open the Mac's **Terminal app** (Cmd+Space, type Terminal, Enter; not the terminal inside the Claude
   app) and type `aws configure --profile koz-deployer`. Paste the **Access key** → Enter, the
   **Secret access key** (click Show, copy) → Enter, type `ap-southeast-2` → Enter, `json` → Enter.

**A5. The Bedrock key for the planner** (only the typed sentence goes to Bedrock).
1. Console search: **Amazon Bedrock** → open it (it opens in Sydney by itself).
2. Left menu **API keys** → **Generate long-term API keys** → expiry **30 days** → **Generate**.
3. Copy the key (it is shown once).
4. In Terminal: `open -e .env` (opens the file in TextEdit). Add this line at the end (or replace the
   line if one starts with `AWS_BEARER_TOKEN_BEDROCK=`), paste your key after the `=`, save (Cmd+S),
   close:
   ```
   AWS_BEARER_TOKEN_BEDROCK=
   ```
   (The planner calls Bedrock in Europe by default, which the project allows; no other line needed.)
5. If Bedrock asks you to request model access for **Nova 2 Lite**: **Model catalog** → **Nova 2 Lite** →
   request access, if a button is shown.

Then tell Claude **"done"**.

## Part B. Claude (you only say yes or no)

1. Read-only checks: that the CLI is `koz-deployer` and not root (Claude stops if it is root); the
   free plan's state and credits; the $1 budget; the role from A2; the template is valid, Sydney
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
5. **You remove Claude's write rights** (they are needed only for the deploy): IAM → **IAM users** →
   **koz-deployer** → tab **Security credentials** → the access key → **Actions** → **Deactivate**
   (and after judging, **Delete**).

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
- Oct 21: the account turned out to be a new-experience project (Google sign-in, no region menu):
  AWS puts projects from Uzbekistan in **Sydney ap-southeast-2** and blocks other regions for
  servers and databases. Islombek chose Sydney (free plan, nothing irreversible) over upgrading for
  Frankfurt; deploy files, the web server's region check and the Uz/Ru/En notice switched. IAM users
  in a project have no console sign-in, so Claude's user `koz-deployer` got a CLI access key that
  Islombek typed into `aws configure` himself. He made the server role, the two policies and the user;
  the IAM console rejected `dynamodb:TransactWriteItems` (not an IAM action): the role now has exactly
  the four table actions the web server uses.
- Oct 21–22, Claude (each create or change shown first and approved): read-only checks (Claude is
  `koz-deployer`; free plan ACTIVE, $120 credits, until 2027-04-14; $1 budget, $0 spent; template
  valid; t3.micro free-plan eligible). Stack try 1 failed: EC2 refuses an apostrophe in a security
  group text ("Ko'z"); CloudFormation removed everything; fixed with a test; the empty failed record
  deleted with Islombek's yes. Try 2: **CREATE_COMPLETE** (also shows servers can be made only
  through CloudFormation). Installed from commit `9c9f5dd`; **HTTPS ready after ~11 minutes**.
- Checked from the Mac (no AWS rights needed): `https://16.178.45.27/` 200 with a valid Let's Encrypt
  IP certificate (6 days, renews by itself); HTTP → HTTPS; HSTS, CSP, no-referrer, nosniff;
  `/api/eye` 404 (no eye on the cloud); events, status and summaries 401 without login; commands 403;
  the runner socket without its token 401. **Judges' view with no login** (headless Chrome,
  `web/review/cloud/judges_probe.mjs`): Live and Trials only, "the owner hasn't shared the demo yet",
  no start or stop button, **no picture loaded, no socket**; the only `<img>` is the hidden large-view
  box, which only the local eye can fill. Found: any unknown path answers 500 `INTERNAL_ERROR`
  instead of 404 (no data in it; web fix for later).
- Running: one t3.micro, 8 GiB encrypted gp3, the fixed IP, table `koz-web` (TTL on), secret
  `koz-owner-password`. About $0.48 a day from the credits. `koz-deployer` tried to read the owner
  password: AccessDenied (explicit deny), as designed.
- Bedrock: not measurable (docs/TRIALS.md, Oct 21): the project denies the API key outside Sydney,
  and in Sydney the new account's daily Bedrock tokens are zero. The rule planner stays the default.
- Oct 22: **the Mac connected and a real job ran through AWS** (rule planner, count people, privacy
  approved, entries and exits counted). Two problems on the way, both fixed with tests:
  - The page said "No device connected" while the Mac was live: **the Mac's clock was 4.9 s fast**
    (measured against time.apple.com and the server), and the page compared the server's times with
    its own clock (3 s limit). Now the server sends its clock with every update and the page corrects
    for the difference (checked in a real browser with the page clock 5 s fast, 5 s slow, 60 s off).
  - Each press of "Create device token" made a new token and disconnected the Mac, and the runner
    reads `.env` only at start. Now the window shows whether the Mac is connected and needs
    "Replace device token…" plus a warning before a new token; the Mac asks for the server address
    and the token once (hidden) and saves them itself (`start-koz-cloud.command`), and asks again if
    the server refuses its token. Also: unknown pages answer 404.
- Server updates without changing the address: a new `Release` parameter replaces only the server
  (fresh install from GitHub, commit in the install log); IP, table, password and device token stay.
  Let's Encrypt allows 5 certificates for the same IP a week: at most 3 more updates before Oct 29.
- Oct 22 (security review): the deployer may change only the stack's own launch template, named by
  its ID in `deploy/iam-deployer-policy.json` (CloudFormation doesn't tag launch templates, so a tag
  can't name it). If the stack is ever made again from scratch, put the new ID there.
- Oct 22, 09:33 UTC: **first server update** (Release `406c222`, Islombek's yes; he first pasted the
  updated deployer policy). CloudFormation made a new launch template version and a new server, moved
  the fixed IP, and removed the old server. HTTPS valid again after ~6 minutes (certificate 2 of 5 this
  week). Checked: the page carries the new code; unknown pages 404; `/api/eye` 404; data 401 without
  login; snapshots carry the server clock; judges' view loads no picture and no socket; one server running.
  (The CLI's first update request went through but its answer was lost; its automatic retry then saw
  the update already finishing.)

