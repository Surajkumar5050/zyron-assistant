<div align="center">

# ⚡ Pikachu Desktop Assistant

<img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
<img src="https://img.shields.io/badge/Platform-Windows-0078D6.svg" alt="Platform">
<img src="https://img.shields.io/badge/AI-Ollama-000000.svg" alt="AI">
<img src="https://img.shields.io/badge/Privacy-100%25%20Local-success.svg" alt="Privacy">
<img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">

**An intelligent, privacy-first desktop assistant that controls your PC via Telegram or Voice**

*Powered by local AI • Zero cloud dependencies • Enterprise-grade security*

[Features](#-features) • [Installation](#-quick-start) • [Usage](#-usage) • [Configuration](#-configuration) • [FAQ](#-faq)

---

</div>

## 🎯 Overview

Pikachu Desktop Assistant transforms your Windows PC into an intelligent, voice-controlled workstation. Built with privacy at its core, it runs **100% locally** using Ollama—no API keys, no cloud services, no data leakage.

### Why Pikachu?

```
✅ Complete Privacy       → All processing happens on your machine
✅ Voice + Remote Control → "Hey Pikachu" or Telegram commands
✅ Zero Subscriptions     → No OpenAI, no monthly fees
✅ Enterprise Security    → Bank-grade local execution
✅ Extensible & Modern    → Python-based, easy to customize
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎮 **Core Capabilities**
- **🗣️ Voice Control** - Wake word detection ("Hey Pikachu")
- **📱 Telegram Remote** - Control PC from anywhere
- **🧠 Local AI Brain** - Powered by Qwen 2.5 Coder (7B)
- **🔒 Stealth Mode** - Runs invisibly in background
- **🚀 Auto-Start** - Launches on Windows boot

</td>
<td width="50%">

### 🛠️ **System Control**
- **💻 System Commands** - Open apps, shutdown, sleep
- **📸 Screenshot & Webcam** - Visual monitoring
- **🔋 Health Monitor** - Battery, RAM, CPU, Disk
- **📂 File Manager** - Browse & download files
- **🌐 Browser Automation** - Launch sites instantly

</td>
</tr>
</table>

### 💬 Example Commands

```
Telegram:
  "Open Chrome"           → Launches browser
  "Take a screenshot"     → Captures & sends image
  "System status"         → RAM, CPU, Battery report
  "Sleep"                 → Puts PC to sleep
  "List my documents"     → Shows files in Documents

Voice:
  "Hey Pikachu, open Spotify"
  "Hey Pikachu, what's my battery level?"
  "Hey Pikachu, take a screenshot"
```

---

## 🛠️ Prerequisites

Before installation, ensure your system meets these requirements:

| Component | Requirement | Download Link |
|-----------|-------------|---------------|
| **OS** | Windows 10/11 (64-bit) | - |
| **Python** | 3.10 or newer | [python.org](https://www.python.org/downloads/) |
| **Ollama** | Latest version | [ollama.com](https://ollama.com/) |
| **Telegram** | Bot token (free) | [@BotFather](https://t.me/BotFather) |
| **Disk Space** | ~6 GB for AI model | - |
| **RAM** | 8 GB minimum (16 GB recommended) | - |

> **💡 Pro Tip:** During Python installation, **check "Add Python to PATH"** for seamless setup.

---

## 🚀 Quick Start

### **Option 1: Automated Setup (Recommended)**

The setup script handles everything automatically:

```bash
# 1. Download and extract the project
git clone https://github.com/YOUR_USERNAME/pikachu-assistant.git
cd pikachu-assistant

# 2. Run the automated installer
setup.bat
```

**What it does:**
- ✅ Verifies Python installation
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Downloads AI model (qwen2.5-coder:7b)
- ✅ Configures auto-start
- ✅ Sets up stealth mode

### **Option 2: Manual Installation**

For advanced users who prefer control:

<details>
<summary><b>Click to expand manual steps</b></summary>

#### 1. Install Ollama & AI Model

```bash
# Download Ollama from https://ollama.com/
# After installation, pull the model:
ollama pull qwen2.5-coder:7b

# Verify it works:
ollama run qwen2.5-coder:7b
# Type /bye to exit
```

#### 2. Clone & Setup Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/pikachu-assistant.git
cd pikachu-assistant

# Create virtual environment
python -m venv venv

# Activate environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Configuration
TELEGRAM_TOKEN=your_bot_token_here

# AI Model
MODEL_NAME=qwen2.5-coder:7b

# Optional: Advanced Settings
LOG_LEVEL=INFO
MAX_TOKENS=2048
```

#### 4. Get Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the token and paste it in `.env`

#### 5. Start the Assistant

```bash
# Option A: Normal mode (shows console)
python main.py

# Option B: Stealth mode (hidden)
run_silent.vbs
```

</details>

---

## ⚙️ Configuration

### Telegram Bot Setup

1. **Create Bot:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot`
   - Choose a name: `My Pikachu Assistant`
   - Choose a username: `mypikachu_bot` (must end with `_bot`)

2. **Get Token:**
   - BotFather will give you a token like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Copy this token

3. **Configure:**
   - Open `.env` file
   - Replace `TELEGRAM_TOKEN=your_bot_token_here` with your actual token
   - Save and restart the assistant

### Voice Control Setup

Voice activation uses wake word detection. To enable:

```python
# In config.py or .env:
ENABLE_VOICE=True
WAKE_WORD="hey pikachu"  # Customize wake phrase
```

### Auto-Start Configuration

The installer automatically adds Pikachu to Windows Startup. To manage:

**Enable:**
```bash
setup.bat  # Re-run installer
```

**Disable:**
```bash
# Delete shortcut from:
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\PikachuAgent.lnk
```

---

## 📖 Usage

### Starting the Assistant

**After installation, you have 3 options:**

```bash
# 1. Auto-start (after reboot)
# → Starts automatically in stealth mode

# 2. Manual stealth start
run_silent.vbs

# 3. Visible console mode (for debugging)
venv\Scripts\activate
python main.py
```

### Basic Commands

#### System Control
```
/open [app]      → Launch application
/shutdown        → Shutdown PC
/sleep           → Sleep mode
/restart         → Reboot system
/lock            → Lock screen
```

#### Information
```
/status          → System health (CPU, RAM, Battery)
/battery         → Battery percentage
/screenshot      → Capture screen
/webcam          → Take webcam photo
```

#### File Management
```
/files           → List files in current directory
/download [path] → Download file to Telegram
/upload          → Upload file from Telegram to PC
```

#### AI Assistant
```
/ask [question]  → Ask the AI anything
/help            → Show all commands
/about           → System information
```

### Voice Commands

Activate with wake word, then speak:

```
"Hey Pikachu, open Chrome"
"Hey Pikachu, what's my battery level?"
"Hey Pikachu, lock my computer"
"Hey Pikachu, take a screenshot"
```

---

## 🔧 Advanced Configuration

### Custom Commands

Add your own commands by editing `commands.py`:

```python
@bot.command("custom")
async def custom_command(ctx):
    # Your code here
    await ctx.send("Custom command executed!")
```

### Model Switching

Change AI model in `.env`:

```env
# Smaller, faster (3B parameters)
MODEL_NAME=qwen2.5-coder:3b

# Larger, smarter (14B parameters)
MODEL_NAME=qwen2.5-coder:14b
```

### Logging

Configure log levels in `.env`:

```env
LOG_LEVEL=DEBUG    # Verbose logging
LOG_LEVEL=INFO     # Standard logging (default)
LOG_LEVEL=WARNING  # Only warnings and errors
LOG_LEVEL=ERROR    # Only errors
```

---

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><b>"Python not found" error</b></summary>

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. **Check "Add Python to PATH"** during installation
3. Restart your terminal
4. Verify: `python --version`

</details>

<details>
<summary><b>"Ollama not found" error</b></summary>

**Solution:**
1. Install Ollama from [ollama.com](https://ollama.com/)
2. Verify: `ollama --version`
3. Pull model: `ollama pull qwen2.5-coder:7b`

</details>

<details>
<summary><b>Bot doesn't respond on Telegram</b></summary>

**Solution:**
1. Check `.env` file has correct token
2. Verify bot is running: Check Task Manager for `python.exe`
3. Test token: Message your bot on Telegram
4. Check logs: `logs/assistant.log`

</details>

<details>
<summary><b>Voice commands not working</b></summary>

**Solution:**
1. Check microphone permissions in Windows Settings
2. Verify `ENABLE_VOICE=True` in `.env`
3. Test wake word detection in console mode
4. Ensure microphone is default input device

</details>

---

## 📁 Project Structure

```
pikachu-assistant/
├── 📄 .gitignore              # Git ignore rules
├── 📄 README.md               # This file - Project documentation
├── 📄 brain.py                # AI brain & Ollama integration
├── 📄 listener.py             # Voice wake word detection
├── 📄 main.py                 # Main application entry point
├── 📄 memory.py               # Conversation memory & context
├── 📄 muscles.py              # System automation & PC control
├── 📄 requirements.txt        # Python dependencies
├── 📄 run_silent.vbs          # Stealth launcher (runs hidden)
├── 📄 setup.bat               # Automated installer & configurator
├── 📄 start_pikachu.bat       # Quick start script
├── 📄 tele_agent.py           # Telegram bot handler
├── 📄 test_mic.py             # Microphone testing utility
├── 📄 .env                    # Environment config (create this)
└── 📂 venv/                   # Virtual environment (auto-created)
```

### 📝 File Descriptions

| File | Purpose |
|------|---------|
| **brain.py** | Core AI engine powered by Ollama (qwen2.5-coder:7b) |
| **listener.py** | Voice wake word detection ("Hey Pikachu") |
| **tele_agent.py** | Telegram bot integration for remote control |
| **muscles.py** | System control (apps, screenshots, files, battery) |
| **memory.py** | Conversation context & chat history management |
| **main.py** | Application orchestrator & startup logic |
| **setup.bat** | One-click installer with progress animations |
| **run_silent.vbs** | Background launcher (stealth mode) |
| **start_pikachu.bat** | Quick start without installation |
| **test_mic.py** | Diagnostic tool for microphone testing |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/AmazingFeature`
3. **Commit** your changes: `git commit -m 'Add AmazingFeature'`
4. **Push** to the branch: `git push origin feature/AmazingFeature`
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pikachu-assistant.git
cd pikachu-assistant

# Create development branch
git checkout -b dev

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

---

## 📝 FAQ

**Q: Is my data sent to any servers?**  
A: No. Everything runs locally on your machine. Ollama processes all AI requests offline.

**Q: Can I use this on Mac/Linux?**  
A: Currently Windows-only due to system automation. Linux/Mac support planned.

**Q: How much RAM does this use?**  
A: ~2-4 GB while idle, ~6-8 GB during AI processing.

**Q: Can I use a different AI model?**  
A: Yes! Any Ollama-compatible model works. Edit `MODEL_NAME` in `.env`.

**Q: Is Telegram required?**  
A: For remote control, yes. Voice-only mode coming soon.

**Q: Can I contribute?**  
A: Absolutely! See [Contributing](#-contributing) section.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License - Free to use, modify, and distribute
© 2025 Pikachu Desktop Assistant
```

---

## 🙏 Acknowledgments

- **[Ollama](https://ollama.com/)** - Local AI infrastructure
- **[Qwen Team](https://github.com/QwenLM/Qwen)** - Qwen 2.5 Coder model
- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** - Telegram integration
- **Community contributors** - Thank you! ⚡

---

## 📞 Support

Need help? We've got you covered:

- 📖 **Documentation:** [Wiki](https://github.com/Surajkumar5050/pikachu-assistant/tree/main/docs)
- 🐛 **Bug Reports:** [Issues](https://github.com/Surajkumar5050/pikachu-assistant/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Surajkumar5050/pikachu-assistant/issues)
- ⭐ **Star this repo** if you find it useful!

---

<div align="center">

**Made with ⚡ and ❤️**

If this project helped you, consider giving it a ⭐ star!

[⬆ Back to Top](#-pikachu-desktop-assistant)

</div>
