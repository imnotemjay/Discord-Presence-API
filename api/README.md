# Discord Presence API - Python Version

Pure Python implementation of Discord user presence and activities API with real-time updates.

## Features

- **FastAPI**: Modern async web framework
- **WebSocket Support**: Real-time presence updates
- **Discord.py**: Discord bot integration
- **Redis/Memory Cache**: Flexible caching options
- **Environment Variables**: Secure configuration

## Quick Start

### Prerequisites
- Python 3.8+
- Discord Bot Token

### Installation

1. **Setup environment:**
```bash
cd python-server
cp .env.example .env
```

2. **Edit .env file:**
```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CLIENT_ID=your_client_id_here
HOST=0.0.0.0
PORT=3000
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the server:**
```bash
python main.py
```

## API Endpoints

### Authentication
All endpoints require: `Authorization: Bot YOUR_BOT_TOKEN`

### REST API
- `GET /v1/users/:userId` - User profile
- `GET /v1/presence/:userId` - User presence  
- `GET /v1/health` - Service health
- `GET /v1/guilds` - Bot guilds

### WebSocket Events
- `authenticate` - Send bot token
- `subscribe_user` - Subscribe to updates
- `presenceUpdate` - Real-time presence changes
- `userUpdate` - User profile changes

## Usage Examples

### Python Client
```python
import aiohttp
import asyncio

async def get_user_presence(user_id):
    headers = {'Authorization': 'Bot YOUR_BOT_TOKEN'}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://localhost:3000/v1/users/{user_id}', headers=headers) as resp:
            return await resp.json()

# Run
data = asyncio.run(get_user_presence('443748099106668544'))
print(data)
```

### cURL
```bash
curl -H "Authorization: Bot YOUR_TOKEN" \
     http://localhost:3000/v1/users/443748099106668544
```

## Deployment

### Render.com
1. Push code to GitHub
2. Create Web Service on Render
3. Set environment variables
4. Deploy

### Environment Variables for Production
```env
DISCORD_BOT_TOKEN=your_production_token
DISCORD_CLIENT_ID=your_client_id
HOST=0.0.0.0
PORT=3000
DEBUG=false
REDIS_URL=your_redis_url
```

## Discord Bot Setup

1. Create bot at https://discord.com/developers/applications
2. Enable intents:
   - Server Members Intent
   - Presence Intent
3. Invite bot to servers

## Architecture

- **FastAPI**: REST API server
- **Socket.IO**: WebSocket handling
- **Discord.py**: Discord bot integration
- **Redis**: Optional caching layer
- **Memory Cache**: Fallback caching

The bot and users must be in the same Discord server for presence data to be available.
