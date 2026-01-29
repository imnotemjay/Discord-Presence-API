# Discord Presence API - 24/7 Uptime Guide

## Overview
Your Discord Presence API is now configured for 24/7 operation with multiple layers of uptime protection.

## Uptime Solutions Implemented

### 1. Render.com Configuration (Primary)
- **Health Check**: `/ping` endpoint monitored every 30 seconds
- **Auto-restart**: Automatic restart on failure
- **Grace Period**: 60 seconds for startup
- **Auto-deploy**: Continuous deployment enabled

### 2. UptimeRobot Integration (Recommended)
- **Monitor URL**: `https://your-app.onrender.com/ping`
- **Check Interval**: Every 1 minute
- **Alert Type**: HTTP(s) monitoring
- **Expected Response**: `{"status": "ok", "timestamp": "..."}`

### 3. Built-in Health Endpoints
- `/ping` - Lightweight endpoint for uptime monitors
- `/v1/health` - Detailed health status including Discord bot and Redis

## Setup Instructions

### Step 1: Deploy to Render.com
1. Push your code to GitHub
2. Connect your repository to Render.com
3. Use the provided `render.yaml` configuration
4. Set environment variables:
   - `DISCORD_BOT_TOKEN`: Your Discord bot token
   - `DISCORD_CLIENT_ID`: Your Discord application ID

### Step 2: Configure UptimeRobot
1. Create a free account at [uptimerobot.com](https://uptimerobot.com)
2. Add new monitor:
   - Monitor Type: HTTP(s)
   - URL: `https://your-app-name.onrender.com/ping`
   - Monitoring Interval: 1 minute
   - Alert Contacts: Your email/phone

### Step 3: Alternative Uptime Services
If you prefer other services:
- **Pingdom**: Free tier available
- **StatusCake**: Free monitoring
- **Better Uptime**: Free with notifications
- **Freshping**: Free uptime monitoring

## Features Added

### Graceful Shutdown
- Handles SIGINT/SIGTERM signals
- Properly closes Discord bot connections
- Closes Redis connections cleanly
- Logs shutdown process

### Health Monitoring
- Lightweight `/ping` endpoint for fast checks
- Detailed `/v1/health` endpoint with service status
- Automatic health check integration with Render

### Error Handling
- Comprehensive error logging
- Graceful degradation when services are unavailable
- Automatic reconnection attempts

## Monitoring Your App

### Check App Status
```bash
# Basic health check
curl https://your-app.onrender.com/ping

# Detailed status
curl https://your-app.onrender.com/v1/health
```

### Log Monitoring
- Render.com provides built-in logs
- Check for "Discord bot starting..." and "Bot online:" messages
- Monitor for any connection errors

## Troubleshooting

### Common Issues
1. **Bot not connecting**: Check Discord token in environment variables
2. **App sleeping**: Ensure UptimeRobot is pinging `/ping` endpoint
3. **Redis connection**: App will fallback to memory cache if Redis fails

### Manual Wake-up
If the app appears to be sleeping:
1. Visit your app URL directly
2. Make an API call to any endpoint
3. Check UptimeRobot status

## Cost Considerations

### Render.com
- Free tier: 750 hours/month (sufficient for 24/7)
- Auto-suspension after 15 minutes of inactivity (prevented by health checks)

### UptimeRobot
- Free tier: 50 monitors, 1-minute intervals
- No cost for basic monitoring

## Next Steps

1. Deploy your updated code to Render.com
2. Set up UptimeRobot monitoring
3. Test the `/ping` endpoint
4. Monitor logs for successful startup
5. Verify Discord bot is online and functioning

Your app should now stay awake 24/7 with automatic monitoring and restart capabilities!
