const axios = require('axios');
const io = require('socket.io-client');

// Configuration
const config = {
  apiUrl: 'http://localhost:3000/v1',
  wsUrl: 'http://localhost:3000',
  botToken: 'YOUR_BOT_TOKEN',
  userId: '1456392490566287529'
};

// Create axios instance with default headers
const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Authorization': `Bot ${config.botToken}`,
    'Content-Type': 'application/json'
  }
});

// REST API Examples
async function restApiExamples() {
  console.log('=== REST API Examples ===\n');

  try {
    // Health check
    console.log('1. Health Check:');
    const health = await api.get('/health');
    console.log(JSON.stringify(health.data, null, 2));
    console.log('\n');

    // Get user profile
    console.log('2. Get User Profile:');
    const user = await api.get(`/users/${config.userId}`);
    console.log(JSON.stringify(user.data, null, 2));
    console.log('\n');

    // Get user presence
    console.log('3. Get User Presence:');
    const presence = await api.get(`/presence/${config.userId}`);
    console.log(JSON.stringify(presence.data, null, 2));
    console.log('\n');

    // Get guilds
    console.log('4. Get Bot Guilds:');
    const guilds = await api.get('/guilds');
    console.log(JSON.stringify(guilds.data, null, 2));
    console.log('\n');

  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
  }
}

// WebSocket Examples
function websocketExamples() {
  console.log('=== WebSocket Examples ===\n');

  const socket = io(config.wsUrl);

  socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    
    // Authenticate
    socket.emit('authenticate', config.botToken);
  });

  socket.on('authenticated', (data) => {
    console.log('WebSocket authenticated:', data);
    
    // Subscribe to user updates
    socket.emit('subscribe_user', config.userId);
    console.log(`Subscribed to updates for user ${config.userId}`);
  });

  socket.on('presenceUpdate', (data) => {
    console.log('Presence Update Received:');
    console.log(JSON.stringify(data, null, 2));
    console.log('---');
  });

  socket.on('userUpdate', (data) => {
    console.log('User Update Received:');
    console.log(JSON.stringify(data, null, 2));
    console.log('---');
  });

  socket.on('authentication_error', (data) => {
    console.error('WebSocket Authentication Error:', data);
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
  });

  socket.on('error', (error) => {
    console.error('WebSocket Error:', error);
  });

  // Keep the script running to receive updates
  process.on('SIGINT', () => {
    console.log('\nDisconnecting...');
    socket.disconnect();
    process.exit(0);
  });
}

// React Component Example
const reactComponentExample = `
// React Component Example
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import axios from 'axios';

const DiscordPresenceCard = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [presence, setPresence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const socket = io('${config.wsUrl}');
    const botToken = '${config.botToken}';

    // WebSocket setup
    socket.on('connect', () => {
      socket.emit('authenticate', botToken);
      socket.emit('subscribe_user', userId);
    });

    socket.on('presenceUpdate', (data) => {
      if (data.userId === userId) {
        setPresence(data);
      }
    });

    socket.on('userUpdate', (data) => {
      if (data.userId === userId) {
        setUser(prev => ({ ...prev, ...data }));
      }
    });

    // Fetch initial data
    const fetchData = async () => {
      try {
        const [userRes, presenceRes] = await Promise.all([
          axios.get(\`/v1/users/\${userId}\`, {
            headers: { 'Authorization': \`Bot \${botToken}\` }
          }),
          axios.get(\`/v1/presence/\${userId}\`, {
            headers: { 'Authorization': \`Bot \${botToken}\` }
          })
        ]);

        setUser(userRes.data);
        setPresence(presenceRes.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    return () => socket.close();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="discord-presence-card">
      {user && (
        <div className="user-info">
          <img 
            src={user.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png'} 
            alt={user.displayName} 
            className="avatar"
          />
          <div className="details">
            <h3>{user.displayName}</h3>
            <p>@{user.username}#{user.discriminator}</p>
            <p>Status: {presence?.status || 'offline'}</p>
            {presence?.activities.map((activity, i) => (
              <div key={i} className="activity">
                <strong>{activity.name}</strong>
                {activity.details && <p>{activity.details}</p>}
                {activity.state && <p>{activity.state}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscordPresenceCard;
`;

// Main execution
async function main() {
  console.log('Discord Presence API - JavaScript Examples\n');
  
  // Run REST API examples
  await restApiExamples();
  
  // Start WebSocket examples
  websocketExamples();
  
  // Show React component example
  console.log('=== React Component Example ===');
  console.log(reactComponentExample);
}

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  restApiExamples,
  websocketExamples,
  reactComponentExample
};
