const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
require('dotenv').config();

const DiscordClient = require('./discord/client');
const apiRoutes = require('./routes/api');
const { connectRedis } = require('./utils/redis');
const logger = require('./utils/logger');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3000;

// Setup socket.io with proper cors
const io = socketIo(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || "*",
    methods: ["GET", "POST"]
  }
});

// Basic middleware setup
app.use(helmet());
app.use(compression());
app.use(cors({
  origin: process.env.CORS_ORIGIN || "*",
  credentials: true
}));
app.use(express.json());

// Health check for monitoring
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    discord: DiscordClient.isConnected() ? 'connected' : 'disconnected',
    redis: global.redisClient ? 'connected' : 'disconnected'
  });
});

// API routes
app.use(`/${process.env.API_VERSION || 'v1'}`, apiRoutes);

// Static files
app.use(express.static('public'));
// WebSocket connection handling
io.on('connection', (socket) => {
  logger.info(`WebSocket client connected: ${socket.id}`);
  
  socket.on('authenticate', (token) => {
    if (token === process.env.DISCORD_BOT_TOKEN) {
      socket.authenticated = true;
      socket.emit('authenticated', { success: true });
      logger.info(`WebSocket client authenticated: ${socket.id}`);
    } else {
      socket.emit('authentication_error', { error: 'Invalid token' });
      socket.disconnect();
    }
  });
  
  socket.on('subscribe_user', (userId) => {
    if (!socket.authenticated) {
      socket.emit('error', { message: 'Authentication required' });
      return;
    }
    
    socket.join(`user_${userId}`);
    logger.info(`Client ${socket.id} subscribed to user ${userId}`);
  });
  
  socket.on('disconnect', () => {
    logger.info(`WebSocket client disconnected: ${socket.id}`);
  });
});

// Initialize everything and start the server
async function startServer() {
  try {
    // Connect to Redis first if configured
    if (process.env.REDIS_URL) {
      await connectRedis();
      logger.info('Redis connected successfully');
    }
    
    // Initialize Discord client (don't fail if it doesn't work)
    try {
      await DiscordClient.init(io);
      logger.info('Discord client initialized');
    } catch (discordError) {
      logger.warn('Discord client failed to initialize, continuing without it:', discordError.message);
    }
    
    // Start the server
    server.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`API available at http://localhost:${PORT}/${process.env.API_VERSION || 'v1'}`);
      logger.info(`WebSocket available at ws://localhost:${PORT}`);
      logger.info(`Demo interface: http://localhost:${PORT}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    DiscordClient.destroy();
    if (global.redisClient) {
      global.redisClient.quit();
    }
    process.exit(0);
  });
});

startServer();
