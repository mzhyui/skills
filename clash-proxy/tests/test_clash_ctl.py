"""Focused unit tests for the Clash proxy controller's safe local behavior."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "clash_ctl.py"
SPEC = importlib.util.spec_from_file_location("clash_ctl", SCRIPT)
assert SPEC and SPEC.loader
clash_ctl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(clash_ctl)


class ClashControllerTests(unittest.TestCase):
    def test_patch_config_ports_enforces_all_required_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.yaml"
            config.write_text(
                "port: 7890\n"
                "socks-port: 7891\n"
                "mixed-port: 9000\n"
                "external-controller: 127.0.0.1:9090\n"
                "proxies:\n"
                "  - name: node\n",
                encoding="utf-8",
            )

            changes = clash_ctl._patch_config_ports(config)

            text = config.read_text(encoding="utf-8")
            self.assertTrue(changes)
            self.assertNotIn("\nport:", f"\n{text}")
            self.assertNotIn("\nsocks-port:", f"\n{text}")
            self.assertIn("mixed-port: 7890", text)
            self.assertIn("external-controller: '127.0.0.1:33541'", text)
            self.assertIn("allow-lan: true", text)

    def test_switch_node_percent_encodes_the_proxy_group(self) -> None:
        group = "🔰 选择节点"
        encoded_group = "%F0%9F%94%B0%20%E9%80%89%E6%8B%A9%E8%8A%82%E7%82%B9"
        with (
            mock.patch.object(clash_ctl, "_detect_active_profile", return_value="ikuuu"),
            mock.patch.object(clash_ctl, "_api_get", return_value={"all": ["JP S01"]}) as get,
            mock.patch.object(clash_ctl, "_api_put", return_value=(True, "HTTP 204")) as put,
            mock.patch.object(clash_ctl, "_health_check", return_value=(True, 0.01)),
            mock.patch.object(clash_ctl.time, "sleep"),
        ):
            clash_ctl.cmd_switch_node("JP S01")

        get.assert_called_once_with(f"proxies/{encoded_group}")
        put.assert_called_once_with(f"proxies/{encoded_group}", {"name": "JP S01"})
        self.assertEqual(clash_ctl.MAIN_GROUP["ikuuu"], group)

    def test_failed_subscription_download_keeps_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config_ikuuu.yaml"
            config.write_text("original: true\n", encoding="utf-8")
            url_file = root / "ikuuu_update.url"
            url_file.write_text("https://example.invalid/subscription\n", encoding="utf-8")
            profiles = {"local": root / "config.yaml", "ikuuu": config}
            failed_download = subprocess.CompletedProcess([], 1, stderr="network failure")

            with (
                mock.patch.object(clash_ctl, "IKUUU_URL_FILE", url_file),
                mock.patch.object(clash_ctl, "PROFILES", profiles),
                mock.patch.object(clash_ctl.subprocess, "run", return_value=failed_download),
                self.assertRaises(SystemExit) as raised,
            ):
                clash_ctl.cmd_update_ikuuu()

            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(config.read_text(encoding="utf-8"), "original: true\n")
            self.assertFalse(list(root.glob(".config_ikuuu.yaml.*.download")))
