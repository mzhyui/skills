#!/usr/bin/env python3
"""
Clash Proxy Controller — unified CLI for profile/node switching with port enforcement.

Port invariants (always enforced):
  mixed-port: 7890            (HTTP + HTTPS + SOCKS5 on one port)
  external-controller: 127.0.0.1:33541  (Clash REST API)

Usage:
  clash_ctl.py status                        # active profile, node, mode, ports
  clash_ctl.py switch-profile local|ikuuu    # switch config profile + reload
  clash_ctl.py switch-node <name>            # switch main proxy group to node
  clash_ctl.py update-ikuuu                  # fetch subscription + patch + reload
  clash_ctl.py fix-ports <config-path>       # patch port invariants into a config
  clash_ctl.py check                         # health-check proxy connectivity
  clash_ctl.py list-nodes [local|ikuuu]      # list nodes for a profile
  clash_ctl.py reload                        # reload active config
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------

CLASH_DIR = Path.home() / ".config" / "clash"

PROFILES = {
    "local": CLASH_DIR / "config.yaml",
    "ikuuu": CLASH_DIR / "config_ikuuu.yaml",
}

IKUUU_URL_FILE = CLASH_DIR / "ikuuu_update.url"

# Port invariants — these are patched into every config before reload
PORT_INVARIANTS = {
    "mixed-port": "7890",
    "external-controller": "'127.0.0.1:33541'",
}

# Top-level YAML keys that are port/network related — we scan for these
PORT_KEYS = {
    "port", "socks-port", "mixed-port", "redir-port", "tproxy-port",
    "external-controller", "allow-lan",
}

# Main proxy group name per profile
MAIN_GROUP = {
    "local": "Proxy",
    "ikuuu": "🔰 选择节点",
}

# Health-check target
CHECK_URL = "https://www.google.com/generate_204"
PROXY_URL = "http://127.0.0.1:7890"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_subscription_url() -> str | None:
    """Read ikuuu subscription URL from the url file."""
    try:
        return IKUUU_URL_FILE.read_text().strip()
    except FileNotFoundError:
        return None


def _detect_active_profile() -> str | None:
    """Detect which profile Clash is currently running by querying the API."""
    # Try to get proxy groups — the group names tell us which profile is active
    data = _api_get("proxies")
    if not data:
        return None
    groups = data.get("proxies", {})
    if "🔰 选择节点" in groups:
        return "ikuuu"
    if "Proxy" in groups:
        # Check if it has the local-style nodes
        all_nodes = groups.get("Proxy", {}).get("all", [])
        if any(n in all_nodes for n in ["jp", "jps", "hk-tc"]):
            return "local"
    return None


_cached_secret: str | None = None
_secret_scanned: bool = False


def _get_api_secret() -> str | None:
    """Find the API secret by reading config files. Never calls the API (avoids recursion)."""
    global _cached_secret, _secret_scanned
    if _secret_scanned:
        return _cached_secret

    # Try reading secret from both config files
    for name, path in PROFILES.items():
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("secret:"):
                        secret = line.split(":", 1)[1].strip().strip("'\"")
                        if secret:
                            _cached_secret = secret
                            _secret_scanned = True
                            return secret
        except (FileNotFoundError, PermissionError):
            continue

    _secret_scanned = True
    return None


def _api_get(path: str) -> dict | None:
    """GET from Clash REST API with auth."""
    url = f"http://127.0.0.1:33541/{path}"
    secret = _get_api_secret()
    headers = {}
    if secret:
        headers["Authorization"] = f"Bearer {secret}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _api_put(path: str, payload: dict) -> tuple[bool, str]:
    """PUT to Clash REST API. Returns (success, message)."""
    url = f"http://127.0.0.1:33541/{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", "application/json")
    secret = _get_api_secret()
    if secret:
        req.add_header("Authorization", f"Bearer {secret}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status in (200, 204)
            return ok, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)


def _api_patch(path: str, payload: dict) -> tuple[bool, str]:
    """PATCH to Clash REST API."""
    url = f"http://127.0.0.1:33541/{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PATCH")
    req.add_header("Content-Type", "application/json")
    secret = _get_api_secret()
    if secret:
        req.add_header("Authorization", f"Bearer {secret}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status in (200, 204)
            return ok, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Port patching
# ---------------------------------------------------------------------------


def _patch_config_ports(config_path: Path) -> list[str]:
    """Patch port invariants into a Clash YAML config file.

    Returns list of changes made (for display). Handles:
    - Replacing existing port key values
    - Removing conflicting port keys (e.g., separate port + socks-port when we want mixed-port)
    - Adding missing invariant keys
    - Preserving allow-lan: true
    """
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        return []

    lines = config_path.read_text().splitlines(keepends=True)
    changes = []
    top_section = True
    new_lines = []
    removed_keys = set()

    # Keys to remove if they conflict with mixed-port
    # (separate port/socks-port are redundant when mixed-port is set)
    REDUNDANT_WITH_MIXED = {"port", "socks-port"}

    for line in lines:
        stripped = line.rstrip("\n\r")

        # Detect end of top-level section
        if top_section and stripped.startswith(
            ("proxies:", "proxy-groups:", "rules:", "proxy-providers:", "rule-providers:")
        ):
            top_section = False

        if top_section:
            # Check if this line is a port-related key
            for key in PORT_KEYS:
                if stripped.startswith(f"{key}:"):
                    # Should we replace it with an invariant value?
                    if key in PORT_INVARIANTS:
                        old_val = stripped.split(":", 1)[1].strip()
                        new_val = PORT_INVARIANTS[key]
                        if old_val != new_val:
                            new_line = f"{key}: {new_val}\n"
                            new_lines.append(new_line)
                            changes.append(f"  {key}: {old_val} → {new_val}")
                        else:
                            new_lines.append(line)
                        break
                    elif key in REDUNDANT_WITH_MIXED:
                        # Remove separate port/socks-port (mixed-port covers both)
                        removed_keys.add(key)
                        changes.append(f"  removed {key}: {stripped.split(':', 1)[1].strip()}")
                        break
                    elif key == "allow-lan":
                        # Ensure allow-lan is true
                        old_val = stripped.split(":", 1)[1].strip()
                        if old_val.lower() != "true":
                            new_lines.append("allow-lan: true\n")
                            changes.append(f"  allow-lan: {old_val} → true")
                        else:
                            new_lines.append(line)
                        break
                    else:
                        # Other port keys (redir-port, tproxy-port) — keep as-is
                        new_lines.append(line)
                        break
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Add any invariant keys that weren't found in the config
    found_keys = set()
    for line in new_lines:
        for key in (*PORT_INVARIANTS, "allow-lan"):
            if line.startswith(f"{key}:"):
                found_keys.add(key)
    for key, val in PORT_INVARIANTS.items():
        if key not in found_keys:
            insert_line = f"{key}: {val}\n"
            new_lines.insert(0, insert_line)
            changes.append(f"  added {key}: {val}")
    if "allow-lan" not in found_keys:
        new_lines.insert(0, "allow-lan: true\n")
        changes.append("  added allow-lan: true")

    if changes:
        config_path.write_text("".join(new_lines))

    return changes


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_status():
    """Show active profile, current node, mode, ports."""
    profile = _detect_active_profile()
    configs = _api_get("configs")
    proxies = _api_get("proxies")

    print("=== Clash Proxy Status ===\n")

    # Profile
    print(f"  Active profile:  {profile or 'UNKNOWN'}")
    if profile:
        print(f"  Config file:     {PROFILES[profile]}")

    # Mode
    mode = configs.get("mode", "UNKNOWN") if configs else "NO API"
    print(f"  Mode:            {mode}")

    # Ports
    if configs:
        mp = configs.get("mixed-port", 0)
        p = configs.get("port", 0)
        sp = configs.get("socks-port", 0)
        print(f"  mixed-port:      {mp}" + (" ✓" if mp == 7890 else " ⚠ expected 7890"))
        if p:
            print(f"  port:            {p}")
        if sp:
            print(f"  socks-port:      {sp}")

    # Current node
    if proxies:
        group_name = MAIN_GROUP.get(profile, "Proxy")
        group = proxies.get("proxies", {}).get(group_name, {})
        now = group.get("now", "UNKNOWN")
        print(f"  Active node:     {now}  (group: {group_name})")

    # Health
    ok, elapsed = _health_check()
    status = f"OK ({elapsed:.2f}s)" if ok else "UNREACHABLE"
    print(f"  Health:          {status}")
    print()


def cmd_switch_profile(profile_name: str):
    """Switch to a different profile: patch ports → reload → verify."""
    if profile_name not in PROFILES:
        print(f"ERROR: Unknown profile '{profile_name}'. Use: {', '.join(PROFILES)}")
        sys.exit(1)

    config_path = PROFILES[profile_name]
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    print(f"Switching to profile: {profile_name}")
    print(f"  Config: {config_path}")

    # Step 1: Patch ports
    print("\n[1/3] Patching port invariants...")
    changes = _patch_config_ports(config_path)
    if changes:
        for c in changes:
            print(c)
    else:
        print("  (no changes needed)")

    # Step 2: Reload
    print("\n[2/3] Reloading Clash config...")
    ok, msg = _api_put("configs?force=true", {"path": str(config_path)})
    if not ok:
        print(f"  ERROR: Reload failed — {msg}")
        sys.exit(1)
    print(f"  Reload OK ({msg})")
    time.sleep(1.5)  # Let Clash settle

    # Step 3: Verify
    print("\n[3/3] Verifying...")
    active = _detect_active_profile()
    if active == profile_name:
        print(f"  ✓ Profile '{profile_name}' is active")
    else:
        print(f"  ⚠ Expected '{profile_name}' but detected '{active}'")

    # Set mode to rule
    mode_ok, mode_msg = _api_patch("configs", {"mode": "rule"})
    if mode_ok:
        print("  ✓ Mode set to rule")

    # Health check
    ok, elapsed = _health_check()
    if ok:
        print(f"  ✓ Proxy healthy ({elapsed:.2f}s)")
    else:
        print("  ⚠ Proxy health check FAILED")
        if profile_name != "local":
            print("  → Falling back to local profile...")
            cmd_switch_profile("local")


def cmd_switch_node(node_name: str):
    """Switch the main proxy group to a specific node."""
    profile = _detect_active_profile()
    if not profile:
        print("ERROR: Cannot detect active profile. Is Clash running?")
        sys.exit(1)

    group_name = MAIN_GROUP.get(profile, "Proxy")
    encoded_group = urllib.parse.quote(group_name, safe="")

    # Verify the node exists in the group
    data = _api_get(f"proxies/{encoded_group}")
    if not data:
        print(f"ERROR: Cannot read proxy group '{group_name}'")
        sys.exit(1)

    available = data.get("all", [])
    if node_name not in available:
        print(f"ERROR: Node '{node_name}' not found in group '{group_name}'")
        print(f"Available nodes:")
        for n in available:
            print(f"  {n}")
        sys.exit(1)

    # Switch
    ok, msg = _api_put(f"proxies/{encoded_group}", {"name": node_name})
    if not ok:
        print(f"ERROR: Switch failed — {msg}")
        sys.exit(1)

    print(f"Switched {group_name} → {node_name}")

    # Health check
    time.sleep(0.5)
    ok, elapsed = _health_check()
    if ok:
        print(f"✓ Healthy ({elapsed:.2f}s)")
    else:
        print("⚠ Health check failed — node may be down")


def cmd_update_ikuuu():
    """Fetch latest ikuuu config from subscription URL, patch ports, reload."""
    url = _read_subscription_url()
    if not url:
        print(f"ERROR: Subscription URL not found at {IKUUU_URL_FILE}")
        sys.exit(1)

    config_path = PROFILES["ikuuu"]
    print(f"Updating ikuuu config...")
    print(f"  URL:  {url}")
    print(f"  Dest: {config_path}")

    # Download to a sibling temporary file so a failed subscription refresh
    # never overwrites the last known-good profile.
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{config_path.name}.",
            suffix=".download",
            dir=config_path.parent,
            delete=False,
        ) as temporary:
            download_path = Path(temporary.name)
    except OSError as e:
        print(f"ERROR: Cannot create temporary download file — {e}")
        sys.exit(1)

    try:
        proc = subprocess.run(
            ["wget", "-q", "--show-progress", "-O", str(download_path), url],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            download_path.unlink(missing_ok=True)
            print(f"ERROR: wget failed (rc={proc.returncode})")
            if proc.stderr:
                print(proc.stderr.strip())
            sys.exit(1)
        print("  ✓ Downloaded")
    except subprocess.TimeoutExpired:
        download_path.unlink(missing_ok=True)
        print("ERROR: Download timed out (30s)")
        sys.exit(1)
    except FileNotFoundError:
        download_path.unlink(missing_ok=True)
        print("ERROR: wget not found")
        sys.exit(1)

    try:
        download_path.replace(config_path)
    except OSError as e:
        download_path.unlink(missing_ok=True)
        print(f"ERROR: Cannot install downloaded config — {e}")
        sys.exit(1)

    # Patch ports
    print("\nPatching port invariants...")
    changes = _patch_config_ports(config_path)
    if changes:
        for c in changes:
            print(c)
    else:
        print("  (no changes needed)")

    # Reload (only if ikuuu is the active profile, or switch to it)
    active = _detect_active_profile()
    if active == "ikuuu":
        print("\nReloading active ikuuu config...")
        ok, msg = _api_put("configs?force=true", {"path": str(config_path)})
        if ok:
            print(f"  ✓ Reload OK")
            time.sleep(1.5)
            ok, elapsed = _health_check()
            if ok:
                print(f"  ✓ Healthy ({elapsed:.2f}s)")
            else:
                print("  ⚠ Health check failed — falling back to local")
                cmd_switch_profile("local")
        else:
            print(f"  ERROR: Reload failed — {msg}")
    else:
        print("\nConfig updated. Run 'switch-profile ikuuu' to activate it.")


def cmd_fix_ports(config_path_str: str | None = None):
    """Patch port invariants into a config file."""
    if config_path_str:
        path = Path(config_path_str).expanduser()
    else:
        # Fix both configs
        for name, path in PROFILES.items():
            print(f"\n--- {name} ({path}) ---")
            if not path.exists():
                print("  (not found, skipping)")
                continue
            changes = _patch_config_ports(path)
            if changes:
                for c in changes:
                    print(c)
            else:
                print("  ✓ All invariants already set")
        return

    if not path.exists():
        print(f"ERROR: Config not found: {path}")
        sys.exit(1)

    changes = _patch_config_ports(path)
    if changes:
        print(f"Patched {path}:")
        for c in changes:
            print(c)
    else:
        print(f"✓ {path} — all invariants already set")


def cmd_check():
    """Health-check proxy connectivity."""
    profile = _detect_active_profile()
    node = None
    proxies = _api_get("proxies")
    if proxies:
        group_name = MAIN_GROUP.get(profile, "Proxy")
        group = proxies.get("proxies", {}).get(group_name, {})
        node = group.get("now")

    print(f"Profile:  {profile or 'UNKNOWN'}")
    print(f"Node:     {node or 'UNKNOWN'}")

    ok, elapsed = _health_check()
    if ok:
        print(f"Proxy:    OK ({elapsed:.2f}s)")
    else:
        print(f"Proxy:    UNREACHABLE")
        sys.exit(1)


def cmd_list_nodes(profile_filter: str | None = None):
    """List available nodes per profile."""
    profiles_to_show = PROFILES if not profile_filter else {profile_filter: PROFILES[profile_filter]}

    for name, path in profiles_to_show.items():
        if not path.exists():
            print(f"\n[{name}] — config not found: {path}")
            continue

        print(f"\n=== {name} ({path.name}) ===")

        # If this is the active profile, use the API
        active = _detect_active_profile()
        if active == name:
            data = _api_get("proxies")
            if data:
                for group_name, info in sorted(data.get("proxies", {}).items()):
                    ptype = info.get("type", "")
                    if ptype in ("Selector", "URLTest", "Fallback", "LoadBalance"):
                        now = info.get("now", "")
                        all_nodes = info.get("all", [])
                        marker = " ← current" if now else ""
                        print(f"\n  [{ptype}] {group_name}{marker}")
                        if now:
                            print(f"    now: {now}")
                        for n in all_nodes:
                            flag = " ← active" if n == now else ""
                            print(f"    • {n}{flag}")
                continue

        # For inactive profiles, parse the YAML file directly
        _list_nodes_from_file(path)


def _list_nodes_from_file(config_path: Path):
    """Extract proxy names and groups from a YAML config file (basic parsing)."""
    try:
        text = config_path.read_text()
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # Extract proxy names
    in_proxies = False
    proxies = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "proxies:":
            in_proxies = True
            continue
        if in_proxies:
            if stripped.startswith("- name:") or stripped.startswith("- {name:"):
                # Extract name
                m = re.search(r"name:\s*['\"]?(.+?)['\"]?\s*[,}]", stripped)
                if not m:
                    m = re.search(r"name:\s*['\"]?(.+?)['\"]?\s*$", stripped)
                if m:
                    proxies.append(m.group(1).strip().strip("'\""))
            elif stripped.startswith(("proxy-groups:", "rules:")):
                in_proxies = False

    # Extract proxy-groups
    in_groups = False
    current_group = None
    groups = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "proxy-groups:":
            in_groups = True
            continue
        if in_groups:
            if stripped.startswith("- name:"):
                m = re.search(r"name:\s*['\"]?(.+?)['\"]?\s*$", stripped)
                if m:
                    current_group = {"name": m.group(1).strip().strip("'\""), "type": "", "proxies": []}
                    groups.append(current_group)
            elif stripped.startswith("type:") and current_group:
                current_group["type"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("proxies:") and current_group:
                # Inline list
                rest = stripped.split(":", 1)[1].strip()
                if rest.startswith("["):
                    items = re.findall(r"['\"]?([^,'\"]+)['\"]?", rest.strip("[]"))
                    current_group["proxies"] = [i.strip() for i in items if i.strip()]
            elif stripped.startswith("- ") and current_group and not stripped.startswith("- name:"):
                item = stripped[2:].strip().strip("'\"")
                if item and not ":" in item:
                    current_group["proxies"].append(item)
            elif stripped.startswith("rules:"):
                in_groups = False

    if proxies:
        print(f"\n  Proxies ({len(proxies)}):")
        for p in proxies:
            print(f"    • {p}")

    if groups:
        print(f"\n  Proxy Groups ({len(groups)}):")
        for g in groups:
            print(f"\n    [{g['type']}] {g['name']}")
            for p in g["proxies"][:10]:
                print(f"      • {p}")
            if len(g["proxies"]) > 10:
                print(f"      ... and {len(g['proxies']) - 10} more")


def cmd_reload():
    """Reload the active config."""
    profile = _detect_active_profile()
    if not profile:
        print("ERROR: Cannot detect active profile")
        sys.exit(1)

    config_path = PROFILES[profile]
    print(f"Reloading {profile} config: {config_path}")

    # Patch ports first
    changes = _patch_config_ports(config_path)
    if changes:
        print("  Port patches applied:")
        for c in changes:
            print(f"  {c}")

    ok, msg = _api_put("configs?force=true", {"path": str(config_path)})
    if ok:
        print(f"  ✓ Reload OK ({msg})")
        time.sleep(1.5)
        # Ensure rule mode
        _api_patch("configs", {"mode": "rule"})
        print("  ✓ Mode: rule")
    else:
        print(f"  ERROR: Reload failed — {msg}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def _health_check(timeout: int = 8) -> tuple[bool, float]:
    """Test proxy reachability via curl."""
    try:
        t0 = time.monotonic()
        proc = subprocess.run(
            [
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "--proxy", PROXY_URL,
                "--connect-timeout", str(timeout),
                "--max-time", str(timeout + 2),
                CHECK_URL,
            ],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        elapsed = time.monotonic() - t0
        http_code = proc.stdout.strip()
        return (http_code == "204" and proc.returncode == 0, elapsed)
    except Exception:
        return (False, float(timeout))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Clash Proxy Controller — profile/node switching with port enforcement"
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    sub.add_parser("status", help="Show active profile, node, mode, ports")
    sub.add_parser("check", help="Health-check proxy connectivity")
    sub.add_parser("reload", help="Reload active config")

    p_switch = sub.add_parser("switch-profile", help="Switch config profile")
    p_switch.add_argument("profile", choices=PROFILES.keys(), help="Profile name")

    p_node = sub.add_parser("switch-node", help="Switch main proxy group to node")
    p_node.add_argument("node", help="Node name (exact match)")

    sub.add_parser("update-ikuuu", help="Fetch ikuuu subscription + patch + reload")

    p_ports = sub.add_parser("fix-ports", help="Patch port invariants into config")
    p_ports.add_argument("config", nargs="?", help="Config path (default: fix both profiles)")

    p_list = sub.add_parser("list-nodes", help="List available nodes")
    p_list.add_argument("profile", nargs="?", choices=PROFILES.keys(), help="Profile to list (default: all)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "status":
        cmd_status()
    elif args.command == "switch-profile":
        cmd_switch_profile(args.profile)
    elif args.command == "switch-node":
        cmd_switch_node(args.node)
    elif args.command == "update-ikuuu":
        cmd_update_ikuuu()
    elif args.command == "fix-ports":
        cmd_fix_ports(args.config)
    elif args.command == "check":
        cmd_check()
    elif args.command == "list-nodes":
        cmd_list_nodes(args.profile)
    elif args.command == "reload":
        cmd_reload()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
