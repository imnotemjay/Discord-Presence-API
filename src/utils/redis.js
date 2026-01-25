const { createClient } = require('redis');
const logger = require('./logger');

let redisClient = null;

async function connectRedis() {
  try {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    
    redisClient = createClient({
      url: redisUrl,
      socket: {
        reconnectStrategy: (retries) => {
          if (retries > 10) {
            logger.error('Redis reconnection failed after 10 attempts');
            return new Error('Redis reconnection failed');
          }
          return Math.min(retries * 50, 1000);
        }
      }
    });

    redisClient.on('error', (error) => {
      logger.error('Redis Client Error:', error);
    });

    redisClient.on('connect', () => {
      logger.info('Redis Client Connected');
    });

    redisClient.on('ready', () => {
      logger.info('Redis Client Ready');
    });

    redisClient.on('end', () => {
      logger.warn('Redis Client Disconnected');
    });

    await redisClient.connect();
    await redisClient.ping();
    
    global.redisClient = redisClient;
    return redisClient;
  } catch (error) {
    logger.error('Failed to connect to Redis:', error);
    throw error;
  }
}

async function disconnectRedis() {
  if (redisClient) {
    try {
      await redisClient.quit();
      redisClient = null;
      global.redisClient = null;
      logger.info('Redis Client Disconnected');
    } catch (error) {
      logger.error('Error disconnecting Redis:', error);
    }
  }
}

function getRedisClient() {
  return redisClient;
}

module.exports = {
  connectRedis,
  disconnectRedis,
  getRedisClient
};
