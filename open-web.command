#!/bin/zsh
# Finder entry point. All implementation lives in web/.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
koz_project_dir="${0:A:h}"
if ! command -v node >/dev/null 2>&1; then
  /usr/bin/osascript -e 'display dialog "Koʻz needs Node.js 22 or newer. Install Node.js, then double-click open-web.command again." buttons {"OK"} default button "OK" with title "Koʻz"'
  exit 1
fi
exec node "$koz_project_dir/web/scripts/open-web.mjs"
