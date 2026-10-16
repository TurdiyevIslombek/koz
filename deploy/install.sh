#!/bin/bash
# Installs the Ko'z web app on the EC2 server. Run once, as root, at first boot by deploy/koz-aws.json.
#   install.sh --ip 1.2.3.4 --secret <secret ARN> --region eu-central-1 --table koz-web [--email you@x]
# What it does, in order (log: /var/log/koz-install.log):
#   1. Node.js 22 (official build, SHA-256 checked), Nginx, Certbot (snap, 5.4+ for IP certificates),
#      AWS CLI (only to read the owner password from Secrets Manager with the server's role).
#   2. Builds the web app from this checkout (web/), runs it as the unprivileged user "koz" on
#      127.0.0.1:4173 behind Nginx (systemd service koz-web).
#   3. Waits until the Elastic IP is this server's, then gets a Let's Encrypt certificate for the IP
#      (staging test first, then the real one; 6-day certificates, renewed automatically).
# Nothing here prints the owner password; it is stored only in /etc/koz/env (root:koz, 0640).
set -euo pipefail

IP="" SECRET="" REGION="" TABLE="" EMAIL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --ip) IP="$2" ;;
    --secret) SECRET="$2" ;;
    --region) REGION="$2" ;;
    --table) TABLE="$2" ;;
    --email) EMAIL="$2" ;;
    *) echo "unknown option $1"; exit 2 ;;
  esac
  shift 2
done
[[ "$IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || { echo "bad --ip"; exit 2; }
[[ "$REGION" =~ ^[a-z0-9-]+$ ]] || { echo "bad --region"; exit 2; }
[[ "$TABLE" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "bad --table"; exit 2; }
[[ "$SECRET" =~ ^arn:aws:secretsmanager:[a-z0-9-]+:[0-9]{12}:secret:[A-Za-z0-9/_+=.@-]+$ ]] || { echo "bad --secret"; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$(cd "$HERE/.." && pwd)"
export DEBIAN_FRONTEND=noninteractive
step() { echo; echo "=== $(date -u +%H:%M:%S) $*"; }

step "1/7 system packages"
apt-get update -y
apt-get install -y nginx curl ca-certificates xz-utils
snap install aws-cli --classic
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot
certbot_ok() { certbot --version 2>&1 | awk '{split($2, v, "."); exit !((v[1] > 5) || (v[1] == 5 && v[2] >= 4))}'; }
if ! certbot_ok; then
  snap refresh certbot --candidate   # IP certificates need Certbot 5.4+ (Let's Encrypt, March 2026)
fi
certbot_ok || { echo "Certbot is older than 5.4: IP certificates need 5.4+"; exit 1; }

step "2/7 Node.js 22 (official build, checksum checked)"
DIST="https://nodejs.org/dist/latest-v22.x"
SUMS="$(curl -fsSL "$DIST/SHASUMS256.txt")"
FILE="$(echo "$SUMS" | awk '/linux-x64\.tar\.xz$/ {print $2}')"
WANT="$(echo "$SUMS" | awk '/linux-x64\.tar\.xz$/ {print $1}')"
curl -fsSL -o "/tmp/$FILE" "$DIST/$FILE"
echo "$WANT  /tmp/$FILE" | sha256sum -c -
rm -rf /opt/node && mkdir -p /opt/node && tar -xJf "/tmp/$FILE" -C /opt/node --strip-components=1 && rm -f "/tmp/$FILE"
ln -sf /opt/node/bin/node /usr/local/bin/node
ln -sf /opt/node/bin/npm /usr/local/bin/npm
node --version

step "3/7 the web app"
id koz >/dev/null 2>&1 || useradd --system --home-dir /var/lib/koz --create-home --shell /usr/sbin/nologin koz
install -d -o koz -g koz -m 0750 /var/lib/koz
cd "$APP/web"
npm ci --no-audit --no-fund
node scripts/build.mjs
npm prune --omit=dev --no-audit --no-fund
chown -R root:root "$APP"
[ -f "$APP/web/server/cloud.mjs" ] || { echo "web/server/cloud.mjs is missing: the web app's cloud mode (Codex) is not in this checkout"; exit 1; }

step "4/7 settings (the owner password comes from Secrets Manager)"
install -d -m 0750 -o root -g koz /etc/koz
PASSWORD="$(aws secretsmanager get-secret-value --region "$REGION" --secret-id "$SECRET" --query SecretString --output text)"
umask 027
cat > /etc/koz/env <<ENV
NODE_ENV=production
PORT=4173
KOZ_PUBLIC_ORIGIN=https://$IP
KOZ_OWNER_PASSWORD=$PASSWORD
KOZ_DATA_DIR=/var/lib/koz
KOZ_TABLE=$TABLE
AWS_REGION=$REGION
ENV
unset PASSWORD
chown root:koz /etc/koz/env
chmod 0640 /etc/koz/env

step "5/7 Nginx (HTTP first, for the certificate check)"
install -d -m 0755 /var/www/koz-acme
sed "s/__IP__/$IP/g" "$HERE/nginx-http.conf" > /etc/nginx/sites-available/koz
ln -sf /etc/nginx/sites-available/koz /etc/nginx/sites-enabled/koz
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

step "6/7 waiting for the Elastic IP, then the certificate"
MINE=""
for _ in $(seq 1 120); do
  TOKEN="$(curl -fsS -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
  MINE="$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 || true)"
  [ "$MINE" = "$IP" ] && break
  sleep 5
done
[ "$MINE" = "$IP" ] || { echo "the Elastic IP $IP is not this server's after 10 minutes"; exit 1; }
if [ -n "$EMAIL" ]; then CONTACT=(--email "$EMAIL"); else CONTACT=(--register-unsafely-without-email); fi
CERT=(certonly --webroot --webroot-path /var/www/koz-acme --ip-address "$IP" --preferred-profile shortlived
      --non-interactive --agree-tos "${CONTACT[@]}")
certbot "${CERT[@]}" --dry-run            # Let's Encrypt staging first: nothing is saved
certbot "${CERT[@]}"                      # then the real, publicly trusted certificate
install -d /etc/letsencrypt/renewal-hooks/deploy
printf '#!/bin/sh\nsystemctl reload nginx\n' > /etc/letsencrypt/renewal-hooks/deploy/koz-reload-nginx
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/koz-reload-nginx
sed "s/__IP__/$IP/g" "$HERE/nginx-https.conf" > /etc/nginx/sites-available/koz
nginx -t
systemctl reload nginx
certbot renew --dry-run                   # renewal works (6-day certificates)

step "7/7 the service"
install -m 0644 "$HERE/koz-web.service" /etc/systemd/system/koz-web.service
systemctl daemon-reload
systemctl enable --now koz-web
for _ in $(seq 1 30); do
  curl -fsS http://127.0.0.1:4173/api/health >/dev/null && break
  sleep 2
done
curl -fsS "https://$IP/api/health" >/dev/null
echo
echo "Ko'z is ready: https://$IP/"
