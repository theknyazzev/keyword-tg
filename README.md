# 🤖 Keyword tg

**Advanced Telegram Channel Monitoring Bot with Real-time Keyword Detection**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v6.9-blue.svg)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

## 🌟 Features

### 🎯 **Core Functionality**
- **Real-time Channel Monitoring** - Monitor multiple Telegram channels simultaneously
- **Keyword Detection** - Advanced pattern matching with customizable keywords
- **Smart Notifications** - Instant alerts when keywords are found
- **Message Storage** - Automatic saving of detected messages to JSON database
- **Pagination Interface** - Navigate through large message lists easily

### 📊 **Analytics & Management**
- **Channel Statistics** - Detailed analytics for each monitored channel
- **Keyword Analytics** - Track keyword frequency and performance
- **Admin Management** - Multi-level admin system with permissions
- **Channel Management** - Easy add/remove channels with verification
- **Message Search** - Powerful search through saved messages

### 🎨 **User Experience**
- **Interactive Menus** - Intuitive button-based navigation
- **Pagination Support** - Browse messages with page navigation (5 per page)
- **Real-time Updates** - Live status updates and statistics
- **Error Handling** - Robust error handling with user-friendly messages
- **Multi-language Support** - Currently supports Russian interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram API credentials (from [my.telegram.org](https://my.telegram.org))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/theknyazzev/keyword-tg.git
   cd stalker-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Telegram API (get from https://my.telegram.org)
API_ID=your_api_id
API_HASH=your_api_hash
PHONE=+1234567890

# Bot Token (get from @BotFather)
BOT_TOKEN=your_bot_token

# Admin User ID (your Telegram user ID)
ADMIN_ID=123456789

# Session Configuration
SESSION_NAME=stalker_session

# Default Keywords (comma-separated)
KEYWORDS=crypto,bitcoin,ethereum,trading,investment
```

### Channel Setup

1. Get channel IDs using [@userinfobot](https://t.me/userinfobot)
2. Add channels through the bot interface: `📺 Каналы → ➕ Добавить канал`
3. Configure keywords: `📝 Ключевые слова → ✏️ Изменить слова`

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and show main menu |
| `/cancel` | Cancel current operation |

## 🔧 Main Menu Structure

```
🎯 Stalker Bot
├── 📺 Каналы (Channels)
│   ├── 📊 Статус каналов (Channel Status)
│   ├── 🔍 Поиск в сообщениях (Message Search)
│   ├── 📝 Ключевые слова (Keywords)
│   ├── 📨 Найденные сообщения (Found Messages)
│   ├── 📈 Статистика каналов (Channel Stats)
│   ├── 📺 Управление каналами (Channel Management)
│   ├── ➕ Добавить канал (Add Channel)
│   └── ➖ Удалить канал (Remove Channel)
└── ⚙️ Настройки (Settings)
    ├── 📝 Ключевые слова (Keywords)
    ├── 📊 Статус системы (System Status)
    ├── ➕ Добавить канал (Add Channel)
    ├── 🧹 Очистить сообщения (Clear Messages)
    └── 👥 Управление админами (Admin Management)
```

## 🏗️ Architecture

### Project Structure

```
keyword-tg/
├── bot/                    # Bot logic and handlers
│   ├── __init__.py
│   ├── control_bot.py     # Main bot controller
│   ├── handlers.py        # Message and callback handlers
│   └── globals.py         # Global state management
├── monitor/               # Channel monitoring module
│   ├── __init__.py
│   └── channel_monitor.py # Telethon-based channel monitor
├── database/              # Database management
│   ├── __init__.py
│   └── json_db.py        # JSON database operations
├── data/                  # Data storage
│   ├── found_messages.json
│   └── settings.json
├── logs/                  # Application logs
├── config.py             # Configuration management
├── utils.py              # Utility functions
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

### Key Components

#### 🤖 **Bot Controller** (`bot/control_bot.py`)
- Handles Telegram Bot API interactions
- Manages user sessions and states
- Processes commands and callbacks

#### 📡 **Channel Monitor** (`monitor/channel_monitor.py`)
- Uses Telethon for real-time channel monitoring
- Implements keyword detection algorithms
- Manages channel access and permissions

#### 💾 **Database** (`database/json_db.py`)
- JSON-based storage system
- Message persistence and retrieval
- Settings and configuration management

## 🔍 Features Deep Dive

### Keyword Detection
- **Case-insensitive matching** - Keywords match regardless of case
- **Whole word matching** - Prevents false positives from partial matches
- **Unicode support** - Full support for international characters
- **Real-time processing** - Instant detection as messages arrive

### Pagination System
- **5 messages per page** - Optimal for mobile viewing
- **Navigation buttons** - ⬅️ Previous / Next ➡️
- **Page indicators** - Shows current page (📄 2/5)
- **Refresh functionality** - 🔄 Update content on demand

### Admin Management
- **Multi-level permissions** - Super admin and regular admin roles
- **Secure access control** - User ID-based authentication
- **Dynamic admin list** - Add/remove admins through interface

## 🛠️ Development

### Adding New Features

1. **New Menu Items**: Modify handlers in `bot/handlers.py`
2. **Database Schema**: Update `database/json_db.py`
3. **Monitoring Logic**: Extend `monitor/channel_monitor.py`
4. **Configuration**: Add variables to `config.py`

### Testing

```bash
# Run basic tests
python test_bot.py

# Test specific components
python -m pytest tests/
```

### Debugging

Enable debug logging in `utils.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Performance

### Specifications
- **Channels**: Monitor up to 100+ channels simultaneously
- **Keywords**: Support for 1000+ keywords
- **Messages**: Handle 10,000+ messages in database
- **Response Time**: < 100ms for most operations
- **Memory Usage**: ~50MB for typical workload

### Optimization Tips
- Limit keywords to reduce false positives
- Regular database cleanup for performance
- Monitor memory usage in production
- Use specific channel filters when possibleines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - For Telegram API interactions
- [aiogram](https://github.com/aiogram/aiogram) - For Bot API framework
- [python-dotenv](https://github.com/theskumar/python-dotenv) - For environment management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/theknyazzev/keyword-tg/issues)
- **Discussions**: [GitHub Discussions](https://github.com/theknyazzev/keyword-tg/discussions)
- **Email**: theknyazzev@gmail.com

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

[Report Bug](https://github.com/theknyazzev/keyword-tg/issues) · [Request Feature](https://github.com/theknyazzev/keyword-tg/issues) · [Documentation](https://github.com/theknyazzev/keyword-tg/wiki)

</div>
