# Discord Presence API

API for Discord user presence and activities with real-time updates.

## Features

- **REST API Endpoints**: Get user profiles and presence data
- **Real-time WebSocket Updates**: Live presence changes via Discord Gateway
- **Caching Layer**: Redis support with in-memory fallback
- **Rate Limiting**: Built-in protection against abuse
- **Security**: Bot token authentication and CORS protection
- **Monitoring**: Health checks and structured logging

## Quick Start

### Prerequisites
- Node.js 16.0.0 or higher
- Discord Bot Token (create at https://discord.com/developers/applications)
- Optional: Redis server for caching

### Installation

1. Clone and setup:
```bash
git clone <repository-url>
cd Discord-Presence-API
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your bot token
```

3. Start the server:
```bash
npm start
```

For development:
```bash
npm run dev
```

## API Endpoints

### Authentication
All endpoints require: `Authorization: Bot YOUR_BOT_TOKEN`

### REST API

#### Get User Profile
```http
GET /v1/users/:userId
```

#### Get User Presence
```http
GET /v1/presence/:userId?guildId=:guildId
```

#### Health Check
```http
GET /v1/health
```

#### Get Guilds
```http
GET /v1/guilds
```

### WebSocket
Connect to `ws://localhost:3000` using Socket.IO.

**Events:**
- `authenticate` - Send bot token
- `subscribe_user` - Subscribe to user updates
- `presenceUpdate` - User presence changed
- `userUpdate` - User profile updated

## Example Usage

### JavaScript/Node.js
```javascript
const axios = require('axios');
const io = require('socket.io-client');

// REST API call
const getUser = async (userId) => {
  const response = await axios.get(`http://localhost:3000/v1/users/${userId}`, {
    headers: {
      'Authorization': 'Bot YOUR_BOT_TOKEN'
    }
  });
  return response.data;
};

// WebSocket connection
const socket = io('http://localhost:3000');

socket.on('connect', () => {
  socket.emit('authenticate', 'YOUR_BOT_TOKEN');
  socket.emit('subscribe_user', '1456392490566287529');
});

socket.on('presenceUpdate', (data) => {
  console.log('Presence updated:', data);
});
```

### React Component
```jsx
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const DiscordPresenceCard = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [presence, setPresence] = useState(null);
  
  useEffect(() => {
    const socket = io('http://localhost:3000');
    
    socket.on('connect', () => {
      socket.emit('authenticate', 'YOUR_BOT_TOKEN');
      socket.emit('subscribe_user', userId);
    });
    
    socket.on('presenceUpdate', (data) => {
      if (data.userId === userId) {
        setPresence(data);
      }
    });
    
    // Fetch initial data
    fetch(`http://localhost:3000/v1/users/${userId}`, {
      headers: { 'Authorization': 'Bot YOUR_BOT_TOKEN' }
    })
    .then(res => res.json())
    .then(setUser);
    
    return () => socket.close();
  }, [userId]);
  
  return (
    <div className="presence-card">
      {user && (
        <div>
          <img src={user.avatar} alt={user.displayName} />
          <h3>{user.displayName}</h3>
          <p>Status: {presence?.status || 'offline'}</p>
          {presence?.activities.map((activity, i) => (
            <div key={i}>
              <strong>{activity.name}</strong>
              {activity.details && <p>{activity.details}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

## Deployment

### Render.com (Recommended)
1. Push your code to GitHub
2. Create a new Web Service on Render
3. Set environment variables in Render dashboard
4. Deploy - your API will be available at `https://your-app.onrender.com`

### Environment Variables for Production
```env
DISCORD_BOT_TOKEN=your_production_bot_token
DISCORD_CLIENT_ID=your_client_id
PORT=3000
NODE_ENV=production
REDIS_URL=your_redis_url
CORS_ORIGIN=https://yourdomain.com
```

## Discord Bot Setup

1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Enable these Gateway Intents:
   - Server Members Intent
   - Presence Intent
5. Copy the bot token to your `.env` file
6. Invite the bot to your servers using this URL format:
   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=0
   ```

## Important Notes

- The bot and users must be in the same Discord server to see presence data
- The bot can be offline and still serve cached data
- Real-time updates require the bot to be online and connected to Discord Gateway
- Rate limiting is automatically enforced to prevent API abuse

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
