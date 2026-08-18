# Chat channels

ClawMetry shows live activity for every OpenClaw channel you have configured. Only channels that are actually set up in your `openclaw.json` appear in the Flow diagram — unconfigured ones are automatically hidden.

Click any channel node in the Flow to see a live chat bubble view with incoming/outgoing message counts.

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Messages, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Reads `~/Library/Messages/chat.db` directly |
| 💚 **WhatsApp** | ✅ Full | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel detection |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel detection |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in web UI sessions |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Via Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Via Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, E2EE support |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat via IRC connection |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** ClawMetry reads your `~/.openclaw/openclaw.json` and only renders the channels you've actually configured. No manual setup required.

