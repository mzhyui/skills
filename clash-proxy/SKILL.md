---
name: clash-proxy
description: "Manage Clash proxy configuration: switch between local (mzhyui.cn) and ikuuu (subscription) profiles, switch proxy nodes (HK/JP/SG/US etc), update ikuuu subscription config, enforce port invariants (mixed-port 7890, controller 33541), health-check, and fallback to local. Use this whenever the user mentions proxy, Clash, switching proxy nodes, changing VPN server, updating proxy config, reloading Clash, fixing proxy ports, checking proxy status, or needs to route traffic through a different region. Also use when the user says things like 'use HK proxy', 'switch to Japan node', 'update ikuuu', 'proxy not working', 'reload clash config', or any variant."
---

# Clash Proxy Manager

Manage the two Clash proxy profiles on this machine, switch nodes, keep ports consistent, and recover when things break.

## The Two Profiles

| Profile | Config file | Source | Nodes | Use case |
|---------|------------|--------|-------|----------|
| **local** | `~/.config/clash/config.yaml` | mzhyui.cn VMess | 3 nodes (jp, jps, hk-tc) + ssh-openai | Default, stable, low-latency |
| **ikuuu** | `~/.config/clash/config_ikuuu.yaml` | Subscription URL | 46 nodes across 16 regions | When more diversity/geo coverage is needed |

Local is the **default fallback** — when in doubt, or when things break, return to local.

## Port Invariants

These values must survive every config switch and subscription update:

| Setting | Required value | Why |
|---------|---------------|-----|
| `mixed-port` | `7890` | Single port for HTTP + HTTPS + SOCKS5 — everything downstream (curl, wget, scripts, proxy_rotator) expects this |
| `external-controller` | `127.0.0.1:33541` | The Clash REST API port — all tooling targets this |
| `allow-lan` | `true` | Lets LAN devices use the proxy |

The `clash_ctl.py` script enforces these automatically on every operation. If a downloaded ikuuu config has different ports (it usually does — 9090, 7890/7891 split), the script patches them before reload.

## Control Script

All operations go through the bundled script:

```bash
python scripts/clash_ctl.py <command> [args]
```

### Commands

| Command | What it does |
|---------|-------------|
| `status` | Show active profile, current node, mode, ports, health |
| `switch-profile local\|ikuuu` | Patch target config's ports → reload Clash → verify |
| `switch-node <name>` | Switch the main proxy group to a specific node |
| `update-ikuuu` | Fetch latest ikuuu subscription → patch ports → reload |
| `fix-ports <config-path>` | Patch port invariants into a config file without reloading |
| `check` | Health-check: can we reach the internet through the proxy? |
| `list-nodes [profile]` | List available nodes for the given profile |

## Workflow: Switching Profiles

When the user asks to switch to a different proxy profile:

1. **Run** `clash_ctl.py switch-profile <name>`
   - The script reads the target config, patches `mixed-port: 7890` and `external-controller: 127.0.0.1:33541`, rewrites any conflicting port keys, then sends `PUT /configs?force=true` to the Clash API
2. **Verify** with `clash_ctl.py status` — confirm the active node list matches the expected profile
3. **Health-check** with `clash_ctl.py check`
4. If health-check fails, **fall back** to local: `clash_ctl.py switch-profile local`

## Workflow: Switching Nodes

When the user asks to use a specific region or node:

1. Run `clash_ctl.py list-nodes` to see what's available in the active profile
2. Run `clash_ctl.py switch-node <name>` with the exact node name
3. Verify with `clash_ctl.py check`

For the local profile, the main proxy group is `Proxy`. For ikuuu, it's `🔰 选择节点`. The script auto-detects which group to target.

## Workflow: Updating iKuuu

When the user asks to update or refresh the ikuuu config:

1. Run `clash_ctl.py update-ikuuu`
   - Downloads from subscription URL → patches ports → reloads
2. Verify with `clash_ctl.py status` and `clash_ctl.py check`

The subscription URL is stored in `~/.config/clash/ikuuu_update.url`. If the download fails, the existing config is kept untouched.

## Auth Secret

The local config uses a `secret: <value>` line for API auth. The ikuuu config has no secret. The script handles both cases — it reads the secret from the active config file and passes `Authorization: Bearer <secret>` when needed.

## Troubleshooting

**Proxy not working after switch:**
1. `clash_ctl.py status` — check if Clash is responding on port 33541
2. `clash_ctl.py fix-ports ~/.config/clash/config.yaml` — ensure port invariants
3. `clash_ctl.py switch-profile local` — fall back to local
4. If Clash isn't responding at all, the process may need a restart: `systemctl restart clash` or kill + relaunch

**All ikuuu nodes failing:**
- `clash_ctl.py switch-profile local` — revert to local immediately
- Then investigate: subscription may be expired, or the URL may have changed

**Port conflict (7890 already in use):**
- Something else grabbed the proxy port. Check with `ss -tlnp | grep 7890`
- Kill the conflicting process or change the proxy port

## Reference

For the full list of nodes per profile and proxy group details, read `references/profiles.md`.
