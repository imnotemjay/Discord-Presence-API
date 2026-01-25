# Discord Presence API

A Python API that provides Discord user presence data like Lanyard - no authentication required.

## 🚀 Quick Start

### Option 1: Use Demo Bot (Easiest)

1. **Add the demo bot** to your Discord server:
   ```
   https://discord.com/oauth2/authorize?client_id=1465105804976984135&permissions=8&integration_type=0&scope=bot
   ```

2. **Clone and run:**
   ```bash
   git clone <your-repo>
   cd Discord-Presence-API
   cd api
   pip install -r requirements.txt
   python main.py
   ```

3. **Test at:** `http://localhost:3000/v1/users/YOUR_DISCORD_ID`

### Option 2: Create Your Own Bot

1. **Create Discord Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create application → Bot → Enable intents:
     - Server Members Intent
     - Presence Intent
     - Guilds Intent

2. **Invite Bot:**
   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&integration_type=0&scope=bot
   ```

3. **Setup .env:**
   ```env
   DISCORD_BOT_TOKEN=your_bot_token
   DISCORD_CLIENT_ID=your_client_id
   PORT=3000
   ```

4. **Deploy on Render.com:**
   - Push to GitHub
   - Create Web Service on Render
   - Set environment variables
   - Deploy

## 📡 API Usage

### REST API (No Auth Required)

```bash
# Get user + presence data
GET /v1/users/:user_id

# Get presence only
GET /v1/presence/:user_id

# Health check
GET /v1/health
```

### Example Response
```json
{
  "success": true,
  "data": {
    "kv": {},
    "discord_user": {
      "id": "443748099106668544",
      "username": "username",
      "global_name": "Display Name",
      "avatar": "avatar_hash"
    },
    "activities": [],
    "discord_status": "online",
    "listening_to_spotify": false
  }
}
```

### WebSocket
```javascript
const socket = io('ws://localhost:3000');
socket.emit('subscribe_user', { user_id: 'USER_ID' });
socket.on('presenceUpdate', (data) => console.log(data));
```

## 🌟 Features

- ✅ **Public API** - No authentication needed
- ✅ **Lanyard Compatible** - Same response format
- ✅ **Real-time Updates** - WebSocket support
- ✅ **Smart Caching** - Works even when bot is offline
- ✅ **Easy Deployment** - Works on Render.com

## 📁 Project Structure

```
Discord-Presence-API/
├── api/
│   ├── main.py           # FastAPI server
│   ├── requirements.txt  # Dependencies
│   ├── .env.example     # Config template
│   └── static/
│       └── index.html   # Demo interface
└── README.md
```

## 🔧 Environment Variables

```env
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CLIENT_ID=your_client_id
PORT=3000
DEBUG=false
REDIS_URL=redis://localhost:6379  # Optional
```

## 🎯 Why This Over Lanyard?

- **Self-hosted** - Full control over your data
- **Python ecosystem** - Easy integration with Python projects
- **Customizable** - Modify the code for your needs
- **No rate limits** - Your own infrastructure

---

**Choose Option 1 for quick testing, or Option 2 for your own production setup! 🚀**

## API Response Format

### User Object
```typescript
interface DiscordUser {
  id: string
  username: string
  displayName: string
  avatar: string | null
  discriminator: string
  publicFlags: number
  banner: string | null
  bannerColor: string | null
  accentColor: number | null
  avatarDecoration: string | null
  premiumType: number
  verified: boolean
  createdAt: string
}
```

### Presence Object
```typescript
interface DiscordPresence {
  userId: string
  status: 'online' | 'idle' | 'dnd' | 'offline' | 'unknown'
  activities: Activity[]
  lastSeen: number | null
  guildId?: string
}
```

### Activity Object
```typescript
interface Activity {
  name: string
  type: number // 0=Playing, 1=Streaming, 2=Listening, 3=Watching, 4=Custom
  details?: string
  state?: string
  applicationId?: string
  assets?: {
    largeImage?: string
    largeText?: string
    smallImage?: string
    smallText?: string
  }
  timestamps?: {
    start?: number
    end?: number
  }
}
```

## License

MIT License - see LICENSE file for details.
