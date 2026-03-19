# Server Deployment Notes

## Current live server
- Host: `194.164.61.102`
- SSH user: `root`
- Live checkout: `/usr/lib/cgi-bin/expedition-narrator`
- Public endpoint: `https://skriptguruai.site/cgi-bin/expedition-narrator/multi_game_expedition_selector_cgi.py`

The legacy Aeon's End-only endpoint is deprecated and may remain unavailable:
- `https://skriptguruai.site/cgi-bin/expedition-narrator/aeons_end_expedition_selector_cgi.py`

## Connect from macOS
```bash
ssh root@194.164.61.102
```

If the Mac has not connected before, install a public key for `root` first by adding the local `~/.ssh/*.pub` key to:
```bash
/root/.ssh/authorized_keys
```

## Update the live checkout
```bash
ssh root@194.164.61.102
cd /usr/lib/cgi-bin/expedition-narrator
git status --short --branch
git pull --ff-only
```

## Verify the CGI script is executable
The live entry point must be executable by Apache:
```bash
cd /usr/lib/cgi-bin/expedition-narrator
ls -l multi_game_expedition_selector_cgi.py
```

Expected mode:
```bash
-rwxr-xr-x
```

If a deployment ever lands without the executable bit, fix it with:
```bash
chmod 755 /usr/lib/cgi-bin/expedition-narrator/multi_game_expedition_selector_cgi.py
```

The repository now tracks this file as executable, so future pulls should preserve the correct mode.

## Verify the live endpoint
From the server or any other machine:
```bash
curl -i "https://skriptguruai.site/cgi-bin/expedition-narrator/multi_game_expedition_selector_cgi.py?game=aeons_end&mage_count=2"
```

Expected result:
- HTTP status `200 OK`
- JSON response body

## If the endpoint returns 500
Check the Apache error log:
```bash
tail -n 80 /var/log/apache2/error.log
```

Common failure modes:
- `Permission denied: AH01241: exec of ... multi_game_expedition_selector_cgi.py failed`
  Fix: restore the executable bit with `chmod 755`.
- `script not found or unable to stat`
  Fix: verify the requested URL path matches the deployed file layout.

## Optional system package maintenance
System package updates are separate from application deploys:
```bash
apt update
apt upgrade -y
reboot
```

This is not required for a normal `git pull`, but a reboot may still be pending after Ubuntu security updates.
