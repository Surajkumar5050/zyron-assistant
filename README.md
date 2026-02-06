<div align="center">

<img src="markdown_themes/header.png" alt="ZYRON Assistant Header" width="100%">

<h1>ZYRON Desktop Assistant</h1>

<p><strong>Your Intelligent Desktop Companion - 100% Local, 100% Private</strong></p>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![AI Engine](https://img.shields.io/badge/AI-Ollama-000000.svg?style=flat-square&logo=ai&logoColor=white)](https://ollama.com)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-00C853.svg?style=flat-square&logo=shield&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-FFC107.svg?style=flat-square)](LICENSE)

</div>

<div align="center">
  <h3>Powerful • Private • Precise</h3>
  <p>Control your Windows PC with voice commands or Telegram - all powered by local AI with zero cloud dependencies</p>
</div>

---

## What Makes ZYRON Special?

ZYRON isn't just another assistant - it's your personal AI that lives entirely on your machine. No subscriptions, no cloud uploads, no privacy concerns. Just pure, powerful automation at your fingertips.

<div align="center">

### Core Features

</div>

<table>
  <tr>
    <td width="33%" align="center">
      <h4>Voice Control</h4>
      <p>Just say "Hey Pikachu" and command your PC naturally</p>
    </td>
    <td width="33%" align="center">
      <h4>Remote Access</h4>
      <p>Control your computer from anywhere via Telegram</p>
    </td>
    <td width="33%" align="center">
      <h4>Smart AI</h4>
      <p>Powered by Qwen 2.5 Coder - understands context and intent</p>
    </td>
  </tr>
  <tr>
    <td width="33%" align="center">
      <h4>100% Private</h4>
      <p>Everything runs locally - no data leaves your PC</p>
    </td>
    <td width="33%" align="center">
      <h4>Zero Cost</h4>
      <p>No API fees, no subscriptions, completely free</p>
    </td>
    <td width="33%" align="center">
      <h4>Production Ready</h4>
      <p>Auto-start, stealth mode, enterprise-grade</p>
    </td>
  </tr>
</table>

---

## See It In Action

<div align="center">

### Real Conversations with ZYRON

<table>
  <tr>
    <td width="50%">
      <img src="markdown_themes/collage1.png" alt="File Search & Battery Monitoring" width="100%">
      <p align="center"><i>Smart file search and battery monitoring with code copying</i></p>
    </td>
    <td width="50%">
      <img src="markdown_themes/collage2.png" alt="System Activities & Storage" width="100%">
      <p align="center"><i>Live browser tracking, app monitoring, and storage analysis</i></p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="markdown_themes/collage3.png" alt="Location & Camera Feed" width="100%">
      <p align="center"><i>Geolocation tracking and live camera feed access</i></p>
    </td>
    <td width="50%">
      <img src="markdown_themes/collage4.png" alt="Audio Recording & File System" width="100%">
      <p align="center"><i>Audio recording and intelligent file system navigation</i></p>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="markdown_themes/collage5.png" alt="Screenshot & System Health" width="50%">
      <p align="center"><i>Screenshots and comprehensive system health monitoring</i></p>
    </td>
  </tr>
</table>
</div>

---

## What Can ZYRON Do?

### System Control
- **Launch & Manage Apps** - Open Chrome, Spotify, VS Code, or any application
- **Power Management** - Sleep, shutdown, restart, or lock your PC
- **File Operations** - Browse, search, and manage files naturally
- **Window Control** - Switch between apps, minimize, maximize

### Monitoring & Intelligence
- **Live Activity Tracking** - See what apps you're running and which browser tabs are open
- **System Health** - Real-time CPU, RAM, disk, and battery monitoring
- **Storage Analysis** - Check available space across all drives
- **Clipboard History** - Access your last 100 copied texts

### Media Capture
- **Screenshots** - Capture your screen on command
- **Camera Feed** - Access your webcam remotely
- **Audio Recording** - Record 10-second clips from system + microphone
- **Instant Sharing** - All media delivered via Telegram

### Smart Search
- **Intelligent File Finder** - "Find that PDF I opened yesterday" - ZYRON understands
- **Recent Files** - Access files by time, type, or keyword
- **Activity Log** - 30-day history of all file access
- **Context-Aware** - Learns your preferences over time

### Location & Network
- **IP Geolocation** - Know where your laptop is
- **Network Info** - Check your connection status
- **Location Tracking** - Useful for lost/stolen device scenarios

---

## Quick Start

### Prerequisites

| Requirement | Version | Download |
|-------------|---------|----------|
| **Windows** | 10/11 (64-bit) | Pre-installed |
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Ollama** | Latest | [ollama.com](https://ollama.com/) |
| **Telegram Bot** | Token | [@BotFather](https://t.me/BotFather) |

### Installation (5 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/Surajkumar5050/zyron-assistant.git
cd zyron-assistant

# 2. Run the automated installer
setup.bat

# That's it! The installer handles:
# ✓ Python environment setup (Python 3.9+)
# ✓ Package installation (pip install -e .)
# ✓ AI model download (qwen2.5-coder:7b)
# ✓ Windows startup integration
# ✓ Stealth mode configuration
```

### Configuration

Create a `.env` file:

```env
TELEGRAM_TOKEN=your_bot_token_here
ALLOWED_TELEGRAM_USERNAME=your_telegram_username
MODEL_NAME=qwen2.5-coder:7b
OFFLINE_MODE=false # Set to true for 100% offline privacy
LOG_LEVEL=INFO
```

### Launch

```bash
# Visible mode (for testing)
start_zyron.bat

# Stealth mode (runs in background)
run_silent.vbs
```

---

## Command Examples

### Voice Commands
```
"Hey Pikachu, what's my battery level?"
"Hey Pikachu, open Spotify"
"Hey Pikachu, take a screenshot"
"Hey Pikachu, show me what I'm doing"
"Hey Pikachu, find that Excel file from yesterday"
"Hey Pikachu, where am I?"
"Hey Pikachu, check storage"
```

### Telegram Commands
```
/activities - See running apps and browser tabs
/screenshot - Capture your screen
/battery - Check battery status
/storage - View disk space across all drives
/location - Get current location
/recordaudio - Record 10 seconds of audio
/camera_on - Start camera feed
/sleep - Put PC to sleep
/copied_texts - View clipboard history
```

### Natural Language (Both Voice & Text)
```
"Open Chrome and go to YouTube"
"What's my battery percentage?"
"Find that PDF I was working on this morning"
"Show me my system resources"
"List files in my downloads folder"
"Clear the recycle bin"
"Send me that document I opened yesterday"
```

---

## Project Architecture

```
zyron-assistant/
│
├── src/
│   └── zyron/
│       ├── main.py                    # Application entry point
│       ├── core/                      # Core System Modules
│       │   ├── brain.py               # AI inference engine
│       │   ├── voice.py               # Voice input/output
│       │   ├── wake_word.py           # Offline Wake Word (Vosk)
│       │   └── memory.py              # Context manager
│       ├── agents/                    # Autonomous Agents
│       │   ├── system.py              # System automation (muscles)
│       │   └── telegram.py            # Telegram bot handler
│       └── features/                  # Feature Modules
│           ├── activity.py            # App & Browser monitoring
│           ├── clipboard.py           # Clipboard history
│           └── files/                 # File System Intelligence
│               ├── finder.py          # Smart search engine
│               └── tracker.py         # File activity logger
│
│
├── browser_extension/         # Chrome extension for tab monitoring
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   ├── popup.js
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
├── firefox_extension/         # Firefox extension for tab monitoring
│   ├── manifest.json
│   ├── background.js
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
│
├── docs/                      # Documentation
│   ├── ACTIVITIES_FEATURE_GUIDE.md
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── CONTRIBUTING.md
│   ├── EXTENSION_INSTALL_GUIDE.md
│   ├── INSTALLATION.md
│   ├── LOCATION_ACCURACY_GUIDE.md
│   └── USER_MANUAL.md
│
├── markdown_themes/           # README assets
│   ├── header.png
│   ├── collage1.png
│   ├── collage2.png
│   ├── collage3.png
│   ├── collage4.png
│   └── collage5.png
│
├── setup.bat                  # Automated installer
├── run_silent.vbs             # Stealth mode launcher
├── start_zyron.bat            # Standard launcher
├── .env                       # Environment configuration (create this)
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
└── LICENSE                    # MIT License
```

---

## Latest Features (v1.3)

### Intelligent File Tracking
- **Automatic Monitoring** - Tracks every file you open across all applications
- **30-Day History** - Complete log with timestamps, apps, and duration
- **40+ File Types** - Documents, images, videos, code, archives, and more

### Natural Language File Search
Just describe what you're looking for:
- "Find that PDF I opened yesterday afternoon"
- "Get me that Excel file from this morning"
- "Send that document I was working on last week"
- "That image I saw 2 hours ago"

### Clipboard History
- **Last 100 Texts** - Never lose a copied snippet again
- **Timestamped** - Know when you copied it
- **Quick Access** - Retrieve via voice or Telegram

### Firefox Integration (New)
- **Native Support** - Tracks active tabs via local history database.
- **Privacy Focused** - No cloud syncing required.

### Offline Voice & Hybrid Mode
- **Offline Wake Word** - Uses Vosk (local) for instant "Hey Pikachu" detection.
- **Hybrid Command** - Falls back to online speech for accuracy, or set `OFFLINE_MODE=true` for 100% local processing.
- **Privacy First** - You control where your audio goes.

---

## Privacy & Security

**Why ZYRON is Different:**

**Zero Cloud Dependencies** - Everything runs on your machine  
**No External APIs** - Your data never leaves your PC  
**No Telemetry** - We don't collect anything  
**Open Source** - Audit the code yourself  
**Local AI** - Ollama processes everything offline  

**Your data is YOURS.**

---

## Advanced Setup

### Browser Activity Monitoring (Advanced)

For the full experience (Screenshots, Tab Control, Media Control):

1.  **Register the Native Host**:
    ```bash
    python src/zyron/scripts/register_native_host.py
    ```
    *(This connects Zyron directly to Firefox securely on your machine)*

2.  **Load the Extension**:
    - **Firefox**: `about:debugging` -> "This Firefox" -> "Load Temporary Add-on" -> Select `firefox_extension/manifest.json`.
    - **Chrome**: Coming soon!

Now Zyron (v1.4) can "see" and "control" your browser in real-time.

---

### Advanced Browser Control (New v1.4) 🦊
- **Smart Logic** - "Close it" knows you mean the YouTube tab you just watched.
- **Ranked Matching** - "Mute Spotify" finds the exact tab instantly.
- **Media Control** - Play/Pause/Next directly from Telegram (no need to open the tab).
- **Tab Capture** - High-quality screenshots of specific tabs (background capture supported).

---

## Frequently Asked Questions

**Q: Is my data safe?**  
A: Absolutely. Everything runs locally on your PC. No cloud services, no external APIs.

**Q: Does it work on Mac/Linux?**  
A: Currently Windows-only due to system automation. Cross-platform support is planned.

**Q: How much RAM does it use?**  
A: 2-4 GB idle, 6-8 GB during active AI processing.

**Q: Can I use different AI models?**  
A: Yes! Any Ollama-compatible model works. Just update `MODEL_NAME` in `.env`

**Q: Does auto-start slow down my PC?**  
A: No. It launches after Windows loads with minimal impact.

**Q: Do I need Telegram?**  
A: For remote control, yes. Voice-only mode is coming in future releases.

---

## Contributing

We love contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/AmazingFeature`
3. **Commit** your changes: `git commit -m 'Add AmazingFeature'`
4. **Push** to the branch: `git push origin feature/AmazingFeature`
5. **Open** a Pull Request

### Development Setup
```bash
git clone https://github.com/Surajkumar5050/zyron-assistant.git
cd zyron-assistant
git checkout -b dev
pip install -e .
pytest tests/
```

---

## License

MIT License - Free to use, modify, and distribute.

```
Copyright © 2025 ZYRON Desktop Assistant
```

See [LICENSE](LICENSE) for full terms.

---

## Acknowledgments

Built with amazing open-source tools:

- [Ollama](https://ollama.com/) - Local AI infrastructure
- [Qwen Team](https://qwenlm.github.io/) - Qwen 2.5 Coder model
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram API wrapper
- All our contributors and testers

---

## Support & Community

- **Documentation**: [Full Wiki](https://github.com/Surajkumar5050/zyron-assistant/tree/main/docs)
- **Bug Reports**: [Issue Tracker](https://github.com/Surajkumar5050/zyron-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Surajkumar5050/zyron-assistant/discussions)

---

<div align="center">

### Star This Project

If ZYRON makes your life easier, give us a star! It helps others discover this project.

**[Back to Top](#zyron-desktop-assistant)**

---

<p><i>Crafted with care for privacy-conscious power users</i></p>

</div>