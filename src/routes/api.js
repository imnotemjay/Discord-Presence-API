const express = require('express');
const rateLimit = require('express-rate-limit');
const DiscordClient = require('../discord/client');
const { getCachedUser, getCachedPresence } = require('../utils/cache');
const logger = require('../utils/logger');

const router = express.Router();

// Setup rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: {
    error: 'Too many requests from this IP, please try again later.'
  }
});

router.use(limiter);

// Check for valid bot token
const checkBotAuth = (req, res, next) => {
  const token = req.headers.authorization?.replace('Bot ', '');
  if (!token || token !== process.env.DISCORD_BOT_TOKEN) {
    return res.status(401).json({ 
      error: 'Unauthorized. Valid bot token required.' 
    });
  }
  next();
};

// GET /api/user/:userId
router.get('/users/:userId', checkBotAuth, async (req, res) => {
  try {
    const { userId } = req.params;
    
    if (!userId || !/^\d+$/.test(userId)) {
      return res.status(400).json({
        error: 'Invalid user ID. Must be a numeric Discord user ID.'
      });
    }

    // Try cache first
    const cachedUser = await getCachedUser(userId);
    if (cachedUser) {
      return res.json(cachedUser);
    }

    // Fetch from Discord
    const user = await DiscordClient.getUser(userId);
    res.json(user);
  } catch (error) {
    logger.error(`Error fetching user ${req.params.userId}:`, error);
    
    if (error.code === 10013) {
      return res.status(404).json({
        error: 'User not found or bot does not have access to this user.'
      });
    }
    
    res.status(500).json({
      error: 'Failed to fetch user data',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// GET /api/presence/:userId
router.get('/presence/:userId', checkBotAuth, async (req, res) => {
  try {
    const { userId } = req.params;
    const { guildId } = req.query;
    
    if (!userId || !/^\d+$/.test(userId)) {
      return res.status(400).json({
        error: 'Invalid user ID. Must be a numeric Discord user ID.'
      });
    }

    if (guildId && !/^\d+$/.test(guildId)) {
      return res.status(400).json({
        error: 'Invalid guild ID. Must be a numeric Discord guild ID.'
      });
    }

    // Try cache first
    const cachedPresence = await getCachedPresence(userId);
    if (cachedPresence && (!guildId || cachedPresence.guildId === guildId)) {
      return res.json(cachedPresence);
    }

    // Fetch from Discord
    const presence = await DiscordClient.getPresence(userId, guildId);
    res.json(presence);
  } catch (error) {
    logger.error(`Error fetching presence for user ${req.params.userId}:`, error);
    
    res.status(500).json({
      error: 'Failed to fetch presence data',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// GET /api/health
router.get('/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      discord: {
        status: DiscordClient.isConnected() ? 'connected' : 'disconnected',
        ready: DiscordClient.ready,
        guilds: DiscordClient.client ? DiscordClient.client.guilds.cache.size : 0
      },
      redis: {
        status: global.redisClient ? 'connected' : 'disconnected'
      },
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.env.npm_package_version || '1.0.0'
    };

    res.json(health);
  } catch (error) {
    logger.error('Health check error:', error);
    res.status(500).json({
      status: 'unhealthy',
      error: 'Health check failed',
      timestamp: new Date().toISOString()
    });
  }
});

// GET /api/guilds
router.get('/guilds', checkBotAuth, async (req, res) => {
  try {
    if (!DiscordClient.isConnected()) {
      return res.status(503).json({
        error: 'Discord client not connected'
      });
    }

    const guilds = DiscordClient.client.guilds.cache.map(guild => ({
      id: guild.id,
      name: guild.name,
      icon: guild.icon ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png` : null,
      memberCount: guild.memberCount,
      ownerId: guild.ownerId,
      features: guild.features
    }));

    res.json({
      guilds,
      total: guilds.length
    });
  } catch (error) {
    logger.error('Error fetching guilds:', error);
    res.status(500).json({
      error: 'Failed to fetch guilds',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Error handling middleware
router.use((error, req, res, next) => {
  logger.error('API Error:', error);
  
  if (error.type === 'entity.parse.failed') {
    return res.status(400).json({
      error: 'Invalid JSON in request body'
    });
  }
  
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
});

// 404 handler
router.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    availableEndpoints: [
      'GET /users/:userId',
      'GET /presence/:userId',
      'GET /health',
      'GET /guilds'
    ]
  });
});

module.exports = router;
