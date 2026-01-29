# Discord Presence API

Get Discord user presence data without authentication. Like Lanyard but self-hosted.

## Quick Start

### Use the Public API

Add bot to server:
```
https://discord.com/oauth2/authorize?client_id=1465105804976984135&permissions=8&integration_type=0&scope=bot
```

API endpoints:
```
https://discord-presence-api-gexg.onrender.com/v1/users/:user_id
https://api.emjay.dev/v1/users/:user_id
```

Example:
```bash
curl https://api.emjay.dev/v1/users/443748099106668544
```

WebSocket:
```javascript
const socket = io('wss://discord-presence-api-gexg.onrender.com');
socket.emit('subscribe_user', { user_id: '443748099106668544' });
```

### Host Your Own

1. Clone:
```bash
git clone https://github.com/imnotemjay/Discord-Presence-API.git
cd Discord-Presence-API/api
```

2. Create Discord bot at [Discord Developers](https://discord.com/developers/applications)
   - Enable Server Members, Presence, and Guilds intents

3. Invite bot:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&integration_type=0&scope=bot
```

4. Setup:
```bash
pip install -r requirements.txt
python main.py
```

5. Deploy to Render.com for 24/7 uptime

## API

### Endpoints
```bash
GET /v1/users/:user_id      # User + presence data
GET /v1/presence/:user_id   # Presence only  
GET /v1/health              # Service status
GET /ping                   # Uptime check
```

### Response Example
```json
{
  "success": true,
  "data": {
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

## Features

- No authentication required
- Lanyard-compatible responses
- Real-time WebSocket updates
- Smart caching (works when bot is offline)
- Easy deployment on Render.com

## Environment Variables

```env
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CLIENT_ID=your_client_id
PORT=3000
DEBUG=false
REDIS_URL=redis://localhost:6379  # Optional
```

## Why This Over Lanyard?

- Self-hosted - you control the data
- Python ecosystem - easy Python integration
- Customizable - modify the code
- No rate limits - your own infrastructure

## 24/7 Uptime

Deploy on Render.com with health checks:
- Automatic restarts on failure
- Health check every 30 seconds
- Free tier covers 24/7 operation

Add UptimeRobot monitoring:
- Monitor `https://your-app.onrender.com/ping`
- 1-minute check interval
- Free monitoring service

## License

MIT
