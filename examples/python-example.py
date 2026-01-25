#!/usr/bin/env python3
"""
Discord Presence API - Python Examples
"""

import asyncio
import aiohttp
import socketio
import json
from typing import Dict, Any

# Configuration
CONFIG = {
    'api_url': 'http://localhost:3000/v1',
    'ws_url': 'http://localhost:3000',
    'bot_token': 'YOUR_BOT_TOKEN',
    'user_id': '1456392490566287529'
}

class DiscordPresenceAPI:
    def __init__(self):
        self.session = None
        self.sio = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.sio:
            await self.sio.disconnect()

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bot {CONFIG["bot_token"]}',
            'Content-Type': 'application/json'
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        async with self.session.get(f'{CONFIG["api_url"]}/health') as response:
            return await response.json()

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information"""
        async with self.session.get(
            f'{CONFIG["api_url"]}/users/{user_id}',
            headers=self._get_headers()
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_presence(self, user_id: str, guild_id: str = None) -> Dict[str, Any]:
        """Get user presence information"""
        url = f'{CONFIG["api_url"]}/presence/{user_id}'
        if guild_id:
            url += f'?guildId={guild_id}'
            
        async with self.session.get(url, headers=self._get_headers()) as response:
            response.raise_for_status()
            return await response.json()

    async def get_guilds(self) -> Dict[str, Any]:
        """Get list of guilds the bot is in"""
        async with self.session.get(
            f'{CONFIG["api_url"]}/guilds',
            headers=self._get_headers()
        ) as response:
            response.raise_for_status()
            return await response.json()

    def setup_websocket(self):
        """Setup WebSocket connection for real-time updates"""
        self.sio = socketio.AsyncClient()
        
        @self.sio.event
        async def connect():
            print('Connected to WebSocket server')
            await self.sio.emit('authenticate', CONFIG['bot_token'])
            
        @self.sio.event
        async def authenticated(data):
            print(f'WebSocket authenticated: {data}')
            await self.sio.emit('subscribe_user', CONFIG['user_id'])
            print(f'Subscribed to updates for user {CONFIG["user_id"]}')
            
        @self.sio.event
        async def presence_update(data):
            print('Presence Update Received:')
            print(json.dumps(data, indent=2))
            print('---')
            
        @self.sio.event
        async def user_update(data):
            print('User Update Received:')
            print(json.dumps(data, indent=2))
            print('---')
            
        @self.sio.event
        async def authentication_error(data):
            print(f'WebSocket Authentication Error: {data}')
            
        @self.sio.event
        async def disconnect():
            print('Disconnected from WebSocket server')
            
        @self.sio.event
        async def error(data):
            print(f'WebSocket Error: {data}')

async def rest_api_examples():
    """Demonstrate REST API usage"""
    print('=== REST API Examples ===\n')
    
    async with DiscordPresenceAPI() as api:
        try:
            # Health check
            print('1. Health Check:')
            health = await api.health_check()
            print(json.dumps(health, indent=2))
            print()
            
            # Get user profile
            print('2. Get User Profile:')
            user = await api.get_user(CONFIG['user_id'])
            print(json.dumps(user, indent=2))
            print()
            
            # Get user presence
            print('3. Get User Presence:')
            presence = await api.get_presence(CONFIG['user_id'])
            print(json.dumps(presence, indent=2))
            print()
            
            # Get guilds
            print('4. Get Bot Guilds:')
            guilds = await api.get_guilds()
            print(json.dumps(guilds, indent=2))
            print()
            
        except Exception as error:
            print(f'API Error: {error}')

async def websocket_examples():
    """Demonstrate WebSocket usage"""
    print('=== WebSocket Examples ===\n')
    
    api = DiscordPresenceAPI()
    api.setup_websocket()
    
    try:
        await api.sio.connect(CONFIG['ws_url'])
        
        # Keep running to receive updates
        print('Listening for real-time updates... Press Ctrl+C to stop')
        await api.sio.wait()
        
    except KeyboardInterrupt:
        print('\nDisconnecting...')
        await api.sio.disconnect()

# Flask Web Application Example
flask_example = '''
# Flask Web Application Example
from flask import Flask, render_template, jsonify, request
import aiohttp
import asyncio
import json

app = Flask(__name__)

DISCORD_API_URL = 'http://localhost:3000/v1'
BOT_TOKEN = 'YOUR_BOT_TOKEN'

async def fetch_discord_data(endpoint, user_id=None):
    """Helper function to fetch data from Discord API"""
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f'Bot {BOT_TOKEN}'}
        url = f'{DISCORD_API_URL}/{endpoint}'
        if user_id:
            url += f'/{user_id}'
            
        async with session.get(url, headers=headers) as response:
            return await response.json()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user/<user_id>')
async def get_user(user_id):
    try:
        data = await fetch_discord_data('users', user_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/presence/<user_id>')
async def get_presence(user_id):
    try:
        data = await fetch_discord_data('presence', user_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
async def health():
    try:
        data = await fetch_discord_data('health')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
'''

# FastAPI Web Application Example
fastapi_example = '''
# FastAPI Web Application Example
from fastapi import FastAPI, HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect
import aiohttp
import json
from typing import Optional

app = FastAPI(title="Discord Presence API Client")

DISCORD_API_URL = 'http://localhost:3000/v1'
BOT_TOKEN = 'YOUR_BOT_TOKEN'

async def fetch_discord_data(endpoint: str, user_id: Optional[str] = None):
    """Helper function to fetch data from Discord API"""
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f'Bot {BOT_TOKEN}'}
        url = f'{DISCORD_API_URL}/{endpoint}'
        if user_id:
            url += f'/{user_id}'
            
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Failed to fetch data")
            return await response.json()

@app.get("/")
async def root():
    return {"message": "Discord Presence API Client"}

@app.get("/health")
async def health_check():
    return await fetch_discord_data('health')

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    return await fetch_discord_data('users', user_id)

@app.get("/presence/{user_id}")
async def get_presence(user_id: str, guild_id: Optional[str] = None):
    url = f'presence/{user_id}'
    if guild_id:
        url += f'?guildId={guild_id}'
    return await fetch_discord_data(url)

@app.get("/guilds")
async def get_guilds():
    return await fetch_discord_data('guilds')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle WebSocket messages here
            await manager.broadcast(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
'''

async def main():
    """Main function to run examples"""
    print('Discord Presence API - Python Examples\n')
    
    # Run REST API examples
    await rest_api_examples()
    
    # Show web framework examples
    print('=== Flask Web Application Example ===')
    print(flask_example)
    print()
    
    print('=== FastAPI Web Application Example ===')
    print(fastapi_example)
    print()
    
    # Ask user if they want to run WebSocket examples
    response = input('Run WebSocket examples? (y/n): ')
    if response.lower() == 'y':
        await websocket_examples()

if __name__ == '__main__':
    asyncio.run(main())
