# AWS day (Oct 19): the click list

Everything is prepared: one CloudFormation template (`deploy/koz-aws.json`) makes the server, the
database, the fixed IP and HTTPS by itself. Your part is clicks, in this order. Take ~45 minutes.
If the console asks you to upgrade the account or to pay for something not listed here: **stop** and
ask Claude.

## Before Oct 19 (at home)

- [ ] **Codex has finished the web app's cloud mode** (`.collab/specs/aws-review.md`). Without it the
      server installs but can't start the app (the install log says so).
- [ ] **The repository is on GitHub and public.** The server downloads Ko'z from there. This is your
      decision: it publishes the code, including the copy of your car's code
      (`koz/brains/flybrain/original/`) and the fly-brain wiring derived from FlyWire (CC BY-NC 4.0:
      credit given in the README, non-commercial). Nothing secret is in git (checked Oct 16). The
      competition needs a public repo anyway. Make an empty public repo named `koz` at
      github.com/new, then in Terminal, in the project folder:
      ```bash
      git remote add origin https://github.com/TurdiyevIslombek/koz.git
      ```
      ```bash
      git push -u origin main
      ```

## On Oct 19

**1. The $1 budget alert (first, before anything else).**
Console search bar → **Billing and Cost Management** → **Budgets** → **Create budget** →
**Use a template** → **Monthly cost budget** → Budget amount **1.00** USD → your email → **Create budget**.
Then, in Billing: **Free tier** (or **Credits**): note the credits left and the plan's end date; it must
be after Nov 1. Budget emails arrive hours late; they are a warning, not a limit.

**2. Region.** Top right → **Europe (Frankfurt) eu-central-1**. Stay there for every step.

**3. The Bedrock key for the planner (on your Mac).**
Console search → **Amazon Bedrock** → left menu **API keys** → **Generate long-term API keys** →
expiry **30 days** → **Generate** → copy the key (it is shown once). In the project's `.env` add two lines:
```
AWS_BEARER_TOKEN_BEDROCK=the-key
AWS_REGION=eu-central-1
```
Then in Terminal:
```bash
.venv/bin/python scripts/score_sentences.py --planner bedrock
```
It plans the 40 test sentences with Amazon Nova 2 Lite and prints the score and the time per plan.
Send Claude the output. **If either 20-sentence set is under 18/20, delete the key line from `.env`:
the rule planner stays the default** (same bar as the Gemma test). If it says the model is not
available: Bedrock → **Model catalog** → **Nova 2 Lite** → request access if a button is shown, then try again.

**4. The server (one stack).**
Console search → **CloudFormation** → **Create stack** → **With new resources (standard)** →
**Upload a template file** → **Choose file** → `deploy/koz-aws.json` → **Next** →
Stack name **koz** → leave the parameters as they are (check `RepoUrl` is your GitHub repo;
`CertEmail` is optional) → **Next** → **Next** → tick **"I acknowledge that AWS CloudFormation might
create IAM resources with custom names"** → **Submit**.
Wait until the status is **CREATE_COMPLETE** (about 5 minutes), then open the **Outputs** tab:
`WebUrl` and `RunnerUrl`. (Creating it accepts Let's Encrypt's terms for the HTTPS certificate.)

**5. Wait about 10 minutes** while the server installs itself, then open `WebUrl`. You see the
Ko'z login page with a valid lock. If not after 15 minutes: **EC2** → **Instances** → **koz-web** →
**Connect** → **Session Manager** → **Connect**, type `sudo tail -50 /var/log/koz-install.log`, and send
Claude the last lines.

**6. The owner password.** The stack's **Outputs** tab shows `OwnerPasswordSecret` (its address).
Console search → **Secrets Manager** → the secret whose name starts with **OwnerPassword** →
**Retrieve secret value** → copy. Log in at `WebUrl` with it. Don't paste it anywhere else.

**7. The runner token.** In the web app: **Create runner token** → **Copy** (shown once; a new one
cancels the old one). In `.env`:
```
KOZ_RUNNER_TOKEN=the-token
```

**8. Connect the Mac** (the `RunnerUrl` from step 4):
```bash
.venv/bin/python -m koz.server --i-own-this-camera --window --cloud wss://THE-IP/v1/runner
```
The web app says the device is connected. Type a job in Setup and watch it.

**9. Before you give judges the link:** open `WebUrl` in a private window on your phone (mobile data):
it loads with a lock; without logging in you can't start anything; unplugging the Mac's internet shows
"offline", never old numbers as live.

## After judging

CloudFormation → **koz** → **Delete** (server, IP, database, role and password secret all go; save
any trial summaries first). Bedrock → **API keys** → delete the key. Keep the $1 budget. Look at
Billing the next day.

Costs (Codex's estimate, to confirm in the console): the server about $9–10 a month, the fixed IP
$3.65 a month, the disk about $1, the password secret $0.40, the database within the free allowance,
Bedrock a few planner calls (each about 400 words of input). On an active Free plan, credits cover
these; the $1 budget warns you if real money is charged.
