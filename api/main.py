import os
import asyncio
import logging
import time
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import socketio
import discord
from discord.ext import commands
import redis.asyncio as redis
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 3000))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    REDIS_URL = os.getenv('REDIS_URL')
    CORS_ORIGIN = os.getenv('CORS_ORIGIN', '*')
    API_VERSION = os.getenv('API_VERSION', 'v1')

config = Config()

# Simple cache system
class SimpleCache:
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def connect_redis(self):
        if config.REDIS_URL:
            try:
                self.redis_client = redis.from_url(config.REDIS_URL)
                await self.redis_client.ping()
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Redis failed, using memory cache: {e}")
                self.redis_client = None
    
    async def set_cache(self, key: str, data: Dict[str, Any]):
        if self.redis_client:
            await self.redis_client.setex(key, self.cache_ttl, json.dumps(data))
        else:
            self.memory_cache[key] = {
                'data': data,
                'timestamp': time.time()
            }
    
    async def get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        if self.redis_client:
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        else:
            cached = self.memory_cache.get(key)
            if cached:
                if time.time() - cached['timestamp'] < self.cache_ttl:
                    return cached['data']
                else:
                    del self.memory_cache[key]
            return None

cache = SimpleCache()

# Graceful shutdown handling
shutdown_event = asyncio.Event()

def signal_handler():
    logger.info("Received shutdown signal, initiating graceful shutdown...")
    shutdown_event.set()

async def graceful_shutdown():
    """Gracefully shutdown all services"""
    logger.info("Starting graceful shutdown...")
    
    # Shutdown Discord bot
    if bot.is_ready():
        await bot.close()
        logger.info("Discord bot shutdown complete")
    
    # Close Redis connection
    if cache.redis_client:
        await cache.redis_client.close()
        logger.info("Redis connection closed")
    
    logger.info("Graceful shutdown complete")

# Discord bot
class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.presences = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        self.sio = None
        self.ready = False
    
    async def on_ready(self):
        self.ready = True
        logger.info(f"Bot online: {self.user}")
        logger.info(f"In {len(self.guilds)} servers")
    
    async def on_presence_update(self, before, after):
        if not after or not after.id:
            return
            
        presence_data = {
            'userId': str(after.id),
            'discord_status': str(after.status),
            'activities': [],
            'lastSeen': time.time()
        }
        
        # Format activities
        for activity in after.activities:
            activity_data = {
                'type': activity.type.value,
                'name': activity.name,
                'details': getattr(activity, 'details', None),
                'state': getattr(activity, 'state', None),
                'application_id': str(activity.application_id) if activity.application_id else None,
                'id': str(activity.id) if activity.id else None,
                'flags': getattr(activity, 'flags', 0),
                'created_at': getattr(activity, 'created_at', None),
                'sync_id': getattr(activity, 'sync_id', None),
                'session_id': getattr(activity, 'session_id', None)
            }
            
            # Add party info if available
            if hasattr(activity, 'party') and activity.party:
                activity_data['party'] = {
                    'id': activity.party.id if activity.party.id else None,
                    'size': getattr(activity.party, 'size', None),
                    'max': getattr(activity.party, 'max', None)
                }
            
            if activity.assets:
                activity_data['assets'] = {
                    'large_image': activity.assets.large_image,
                    'large_text': activity.assets.large_text,
                    'small_image': activity.assets.small_image,
                    'small_text': activity.assets.small_text
                }
            
            if activity.timestamps:
                activity_data['timestamps'] = {
                    'start': activity.timestamps.start.timestamp() if activity.timestamps.start else None,
                    'end': activity.timestamps.end.timestamp() if activity.timestamps.end else None
                }
            
            presence_data['activities'].append(activity_data)
        
        await cache.set_cache(f"presence:{after.id}", presence_data)
        
        # Send to WebSocket clients
        if self.sio:
            await self.sio.emit('presenceUpdate', presence_data)
    
    async def on_member_update(self, before, after):
        if before.display_name != after.display_name or before.avatar != after.avatar:
            user_data = {
                'id': str(after.id),
                'username': after.name,
                'global_name': after.global_name if hasattr(after, 'global_name') else after.display_name,
                'display_name': after.display_name,
                'avatar': str(after.avatar) if after.avatar else None,
                'discriminator': after.discriminator,
                'public_flags': after.public_flags.value if after.public_flags else 0,
                'banner': str(after.banner) if after.banner else None,
                'accent_color': after.accent_color.value if after.accent_color else None,
                'bot': after.bot,
                'avatar_decoration_data': getattr(after, 'avatar_decoration_data', None),
                'collectibles': getattr(after, 'collectibles', None),
                'primary_guild': getattr(after, 'primary_guild', None),
                'display_name_styles': getattr(after, 'display_name_styles', None)
            }
            
            await cache.set_cache(f"user:{after.id}", user_data)
            
            if self.sio:
                await self.sio.emit('userUpdate', user_data)

bot = DiscordBot()

# Socket.IO setup
sio = socketio.AsyncServer(cors_allowed_origins=config.CORS_ORIGIN)
app = FastAPI(title="Discord Presence API", version="1.0.0")

# Mount Socket.IO
sio_app = socketio.ASGIApp(sio, app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Discord Presence API", 
        "version": "1.0.0",
        "info": "Public Discord presence API - no authentication required",
        "monitored_user_count": len(cache.memory_cache) if not cache.redis_client else "connected",
        "developed_by": "MJ",
        "github": "https://github.com/imnotemjay/"
    }

@app.get(f"/{config.API_VERSION}/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "discord": {
            "status": "connected" if bot.ready else "disconnected",
            "ready": bot.ready,
            "guilds": len(bot.guilds) if bot.ready else 0
        },
        "redis": {
            "status": "connected" if cache.redis_client else "disconnected"
        },
        "uptime": "running"
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint for uptime monitoring services like UptimeRobot"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/debug")
async def debug():
    """Debug endpoint to check bot status and configuration"""
    return {
        "config": {
            "discord_bot_token_set": bool(config.DISCORD_BOT_TOKEN),
            "discord_client_id_set": bool(config.DISCORD_CLIENT_ID),
            "host": config.HOST,
            "port": config.PORT,
            "debug": config.DEBUG,
            "redis_url_set": bool(config.REDIS_URL)
        },
        "bot": {
            "ready": bot.ready,
            "user": str(bot.user) if bot.user else None,
            "guilds": len(bot.guilds) if bot.ready else 0
        },
        "cache": {
            "redis_connected": bool(cache.redis_client),
            "memory_cache_size": len(cache.memory_cache)
        }
    }

@app.get(f"/{config.API_VERSION}/users/{{user_id}}")
async def get_user(user_id: str):
    """Get user profile + presence data (Lanyard style)"""
    try:
        user_data = None
        presence_data = None
        
        # Get cached data
        cached_user = await cache.get_cache(f"user:{user_id}")
        if cached_user:
            user_data = cached_user
        
        cached_presence = await cache.get_cache(f"presence:{user_id}")
        if cached_presence:
            presence_data = cached_presence
        
        # Fetch fresh data if bot is ready
        if bot.ready and not user_data:
            try:
                discord_user = await bot.fetch_user(int(user_id))
                user_data = {
                    'id': str(discord_user.id),
                    'username': discord_user.name,
                    'global_name': discord_user.global_name if hasattr(discord_user, 'global_name') else discord_user.display_name,
                    'display_name': discord_user.display_name,
                    'avatar': str(discord_user.avatar) if discord_user.avatar else None,
                    'discriminator': discord_user.discriminator,
                    'public_flags': discord_user.public_flags.value if discord_user.public_flags else 0,
                    'banner': str(discord_user.banner) if discord_user.banner else None,
                    'accent_color': discord_user.accent_color.value if discord_user.accent_color else None,
                    'bot': discord_user.bot,
                    'avatar_decoration_data': getattr(discord_user, 'avatar_decoration_data', None),
                    'collectibles': getattr(discord_user, 'collectibles', None),
                    'primary_guild': getattr(discord_user, 'primary_guild', None),
                    'display_name_styles': getattr(discord_user, 'display_name_styles', None)
                }
                
                await cache.set_cache(f"user:{user_id}", user_data)
            except discord.NotFound:
                return {
                    "success": False,
                    "error": {
                        "code": 404,
                        "message": "User not found"
                    }
                }
            except discord.Forbidden:
                return {
                    "success": False,
                    "error": {
                        "code": 403,
                        "message": "Access denied"
                    }
                }
        
        # Get presence data if needed
        if bot.ready and not presence_data:
            try:
                for guild in bot.guilds:
                    try:
                        member = await guild.fetch_member(int(user_id))
                        if member.presence:
                            presence_data = {
                                'discord_status': str(member.presence.status),
                                'active_on_discord_desktop': member.presence.desktop,
                                'active_on_discord_mobile': member.presence.mobile,
                                'active_on_discord_web': member.presence.web,
                                'active_on_discord_embedded': False,
                                'listening_to_spotify': any(a.name == 'Spotify' for a in member.presence.activities),
                                'activities': [],
                                'spotify': None
                            }
                            
                            # Format activities
                            for activity in member.presence.activities:
                                activity_data = {
                                    'type': activity.type.value,
                                    'name': activity.name,
                                    'details': getattr(activity, 'details', None),
                                    'state': getattr(activity, 'state', None),
                                    'application_id': str(activity.application_id) if activity.application_id else None,
                                    'id': str(activity.id) if activity.id else None,
                                    'flags': getattr(activity, 'flags', 0),
                                    'created_at': getattr(activity, 'created_at', None),
                                    'sync_id': getattr(activity, 'sync_id', None),
                                    'session_id': getattr(activity, 'session_id', None)
                                }
                                
                                # Add party info if available
                                if hasattr(activity, 'party') and activity.party:
                                    activity_data['party'] = {
                                        'id': activity.party.id if activity.party.id else None,
                                        'size': getattr(activity.party, 'size', None),
                                        'max': getattr(activity.party, 'max', None)
                                    }
                                
                                if activity.assets:
                                    activity_data['assets'] = {
                                        'large_image': activity.assets.large_image,
                                        'large_text': activity.assets.large_text,
                                        'small_image': activity.assets.small_image,
                                        'small_text': activity.assets.small_text
                                    }
                                
                                if activity.timestamps:
                                    activity_data['timestamps'] = {
                                        'start': activity.timestamps.start.timestamp() if activity.timestamps.start else None,
                                        'end': activity.timestamps.end.timestamp() if activity.timestamps.end else None
                                    }
                                
                                presence_data['activities'].append(activity_data)
                            
                            # Handle Spotify
                            if presence_data['listening_to_spotify']:
                                spotify_activity = next((a for a in member.presence.activities if a.name == 'Spotify'), None)
                                if spotify_activity:
                                    # Extract album art from assets
                                    album_art_url = None
                                    if spotify_activity.assets:
                                        if spotify_activity.assets.large_image:
                                            if spotify_activity.assets.large_image.startswith('spotify:'):
                                                album_art_url = f"https://i.scdn.co/image/{spotify_activity.assets.large_image.replace('spotify:', '')}"
                                            else:
                                                album_art_url = f"https://cdn.discordapp.com/app-assets/{spotify_activity.application_id}/{spotify_activity.assets.large_image}.png"
                                    
                                    presence_data['spotify'] = {
                                        'track_id': spotify_activity.sync_id,
                                        'timestamps': {
                                            'start': spotify_activity.timestamps.start.timestamp() if spotify_activity.timestamps.start else None,
                                            'end': spotify_activity.timestamps.end.timestamp() if spotify_activity.timestamps.end else None
                                        },
                                        'song': spotify_activity.details,
                                        'artist': spotify_activity.state,
                                        'album_art_url': album_art_url,
                                        'album': spotify_activity.assets.large_text if spotify_activity.assets and spotify_activity.assets.large_text else None
                                    }
                            
                            await cache.set_cache(f"presence:{user_id}", presence_data)
                            break
                    except (discord.NotFound, discord.Forbidden):
                        continue
                        
            except Exception:
                pass
        
        # Return Lanyard-style response
        if user_data:
            return {
                "success": True,
                "data": {
                    "kv": {},
                    "discord_user": user_data,
                    "activities": presence_data.get('activities', []) if presence_data else [],
                    "discord_status": presence_data.get('discord_status', 'offline') if presence_data else 'offline',
                    "active_on_discord_web": presence_data.get('active_on_discord_web', False) if presence_data else False,
                    "active_on_discord_desktop": presence_data.get('active_on_discord_desktop', False) if presence_data else False,
                    "active_on_discord_mobile": presence_data.get('active_on_discord_mobile', False) if presence_data else False,
                    "active_on_discord_embedded": presence_data.get('active_on_discord_embedded', False) if presence_data else False,
                    "listening_to_spotify": presence_data.get('listening_to_spotify', False) if presence_data else False,
                    "spotify": presence_data.get('spotify') if presence_data else None
                }
            }
        
        return {
            "success": False,
            "error": {
                "code": 404,
                "message": "User not found"
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return {
            "success": False,
            "error": {
                "code": 500,
                "message": "Failed to fetch user data"
            }
        }

@app.get(f"/{config.API_VERSION}/presence/{{user_id}}")
async def get_presence(user_id: str, guild_id: Optional[str] = None):
    """Get user presence data only"""
    try:
        cached_presence = await cache.get_cache(f"presence:{user_id}")
        if cached_presence:
            return {
                "success": True,
                "data": cached_presence
            }
        
        # Return offline presence if no data
        offline_presence = {
            'userId': user_id,
            'discord_status': 'offline',
            'active_on_discord_desktop': False,
            'active_on_discord_mobile': False,
            'active_on_discord_web': False,
            'active_on_discord_embedded': False,
            'listening_to_spotify': False,
            'activities': [],
            'lastSeen': None,
            'guildId': guild_id
        }
        
        return {
            "success": True,
            "data": offline_presence
        }
        
    except Exception as e:
        logger.error(f"Error fetching presence for user {user_id}: {e}")
        return {
            "success": False,
            "error": {
                "code": 500,
                "message": "Failed to fetch presence data"
            }
        }

@app.get(f"/{config.API_VERSION}/guilds")
async def get_guilds():
    """Get bot guilds"""
    try:
        if not bot.ready:
            return {
                "success": False,
                "error": {
                    "code": 503,
                    "message": "Bot not ready"
                }
            }
        
        guilds_data = []
        for guild in bot.guilds:
            guild_data = {
                'id': str(guild.id),
                'name': guild.name,
                'icon': str(guild.icon) if guild.icon else None,
                'memberCount': guild.member_count,
                'ownerId': str(guild.owner_id) if guild.owner else None,
                'features': list(guild.features)
            }
            guilds_data.append(guild_data)
        
        return {
            "success": True,
            "data": {
                'guilds': guilds_data,
                'total': len(guilds_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching guilds: {e}")
        return {
            "success": False,
            "error": {
                "code": 500,
                "message": "Failed to fetch guilds"
            }
        }

# Socket.IO events
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def subscribe_user(sid, data):
    user_id = data.get('user_id')
    if user_id:
        await sio.enter_room(sid, f"user_{user_id}")
        logger.info(f"Client {sid} subscribed to user {user_id}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

# Startup and shutdown
@app.on_event("startup")
async def startup_event():
    await cache.connect_redis()
    
    # Start Discord bot in background
    try:
        bot.sio = sio
        asyncio.create_task(start_discord_bot())
        logger.info("Discord bot startup initiated...")
    except Exception as e:
        logger.error(f"Failed to initiate Discord bot startup: {e}")

async def start_discord_bot():
    """Start Discord bot with proper error handling"""
    try:
        await bot.start(config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token - check your DISCORD_BOT_TOKEN environment variable")
    except discord.PrivilegedIntentsRequired:
        logger.error("Privileged intents required - enable Server Members and Presence intents in Discord Developer Portal")
    except Exception as e:
        logger.error(f"Discord bot failed to start: {e}")
        logger.info("API will continue running without Discord bot functionality")

@app.on_event("shutdown")
async def shutdown_event():
    if bot.is_ready():
        await bot.close()
    if cache.redis_client:
        await cache.redis_client.close()

# Run server
if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    # Create server instance
    uvicorn_config = uvicorn.Config(
        sio_app,
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
    server = uvicorn.Server(uvicorn_config)
    
    async def run_server():
        """Run server with graceful shutdown handling"""
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await graceful_shutdown()
    
    # Run with shutdown event monitoring
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Application shutdown complete")
        sys.exit(0)
