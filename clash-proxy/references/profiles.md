# Clash Proxy Profiles Reference

## Local Profile (config.yaml)

Default, stable, low-latency. Self-hosted mzhyui.cn VMess nodes.

### Nodes (4)

- jp: vmess+wss+tls on webvt.mzhyui.cn:443 (Japan primary)
- jps: vmess+wss+tls on webvts.mzhyui.cn:443 (Japan secondary)
- hk-tc: vmess+wss+tls on webtcl.mzhyui.cn:443 (Hong Kong)
- ssh-openai: socks5 on 127.0.0.1:7891 (local SSH tunnel for ChatGPT/OpenAI)

### Proxy Groups

- Proxy (select): Auto, load-balance, relay, jp, jps, hk-tc -- main selector
- Auto (url-test): jps, hk-tc -- auto-pick lowest latency
- load-balance: jps, hk-tc -- round-robin
- relay: hk-tc then jp -- HK to JP chain
- Proxy-JP (select): jp, jps, hk-tc -- Japan-targeted traffic
- Proxy-HK (url-test): hk-tc -- HK-targeted traffic
- OpenAI (select): ssh-openai, jps, jp -- ChatGPT/API

### Auth

Stored as `secret: <value>` in the config file (read dynamically by `clash_ctl.py`).

---

## iKuuu Profile (config_ikuuu.yaml)

Subscription-based hub with 46 nodes across 16 regions. More geo diversity.

### Subscription URL

Stored in: ~/.config/clash/ikuuu_update.url

### Nodes by Region (46 total)

- HK: 11 nodes (S01-S11), SS aes-256-gcm + vmess, x0.8-x1 rate
- JP: 11 nodes (S01-S11), SS + vmess, x0.01-x1 rate. S05/S06 download-dedicated at x0.01
- JP Free: 7 nodes (Ver.2-Ver.9), vmess, free/unmetered
- SG: 3 nodes (S01-S03), SS, x2 IEPL premium
- TW: 1 node (S01), SS, x2 IEPL
- US: 2 nodes (S01-S02), SS, x1.5 IEPL
- GB, AR, RU, TR, KR, IN, DE, CA, AU, FR, UA: 1 node each, SS, x1

### Key Proxy Groups

- main selector: all traffic routes through here
- bilibili/iqiyi: Chinese streaming, default DIRECT
- Steam login/download: default DIRECT
- Steam store/community: via main selector
- academic: WOS, PubMed, IEEE, Nature, Elsevier, Springer, Wiley, ACM -- default DIRECT
- ad-block: REJECT toggle
- catch-all: unmatched traffic, via main selector

### Auth

No secret (open API)

---

## Port Specification (enforced by clash_ctl.py)

- mixed-port: 7890 (HTTP + HTTPS + SOCKS5 unified)
- external-controller: 127.0.0.1:33541 (Clash REST API)
- allow-lan: true

Separate port/socks-port keys are removed when present (mixed-port covers both).
