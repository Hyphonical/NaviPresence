# NaviPresence 🎵

A sleek Discord Rich Presence integration for Navidrome, displaying your currently playing music with album art and timestamps. Built with Python for simplicity and style.

## ✨ Features

- 🎧 Real-time Discord Rich Presence updates
- 🖼️ Dynamic album cover art support
- 🔄 Auto-reconnection for stable connections
- 🎨 Rich logging with colorful console output
- 🚀 Easy setup with environment variables

## 📋 Prerequisites

- Python 3.8+
- A Navidrome server instance
- Discord application with bot token and user token

## 🛠️ Installation

1. **Clone or download** the repository:
   ```bash
   git clone https://github.com/Hyphonical/NaviPresence.git
   cd navipresence
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirement.txt
   ```

3. **Configure environment**:
   - Copy .env.example to .env
   - Fill in your details (see Configuration section below)

## ⚙️ Configuration

Edit your .env file with the following variables:

```env
# Navidrome server details
NAVIDROME_HOST=https://your-navidrome-server.com
NAVIDROME_USER=your_username
NAVIDROME_PASSWORD=your_password

# Discord application details
DISCORD_USER_TOKEN=your_discord_user_token
DISCORD_BOT_APPLICATION_ID=your_bot_application_id
```

### 🔑 Getting Tokens

- **Navidrome**: Use your server URL and login credentials
- **Discord User Token**: 
  1. Open Discord in a browser
  2. Press F12 → Network tab
  3. Send a message, find the Authorization header
- **Discord Bot Application ID**:
  1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
  2. Create a new application
  3. Copy the Application ID from General Information

## 🚀 Usage

1. **Start the application**:
   ```bash
   python Main.py
   ```

2. **Play music** in Navidrome – Rich Presence will update automatically!

3. **Stop gracefully** with `Ctrl+C`

The app will:
- 🔍 Poll Navidrome every 15 seconds for current song
- 🎮 Update Discord with song details and cover art
- 📝 Log activity in a colorful console
- 🔄 Handle reconnections if Discord disconnects

## 📁 Project Structure

```
NaviPresence/
├── Main.py              # Main application logic
├── Config.py            # Configuration constants
├── Utils/
│   ├── RPC.py           # Discord WebSocket RPC handler
│   └── Logger.py        # Rich console logging
├── .env.example         # Environment template
├── requirement.txt      # Python dependencies
└── ruff.toml            # Code formatting config
```

## 🤝 Contributing

Feel free to open issues or PRs!

## 📄 License

MIT License – see LICENSE file for details.