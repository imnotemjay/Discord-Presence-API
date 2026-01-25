const logger = require('./logger');

// Simple memory cache when Redis isn't available
const memoryCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function setCache(key, data) {
  memoryCache.set(key, {
    data,
    timestamp: Date.now()
  });
}

function getCache(key) {
  const cached = memoryCache.get(key);
  if (!cached) return null;
  
  if (Date.now() - cached.timestamp > CACHE_TTL) {
    memoryCache.delete(key);
    return null;
  }
  
  return cached.data;
}

async function cacheUser(userId, userData) {
  const key = `user:${userId}`;
  
  try {
    if (global.redisClient) {
      await global.redisClient.setEx(key, CACHE_TTL / 1000, JSON.stringify(userData));
    } else {
      setCache(key, userData);
    }
    
    logger.debug(`Cached user data for ${userId}`);
  } catch (error) {
    logger.error('Error caching user data:', error);
    setCache(key, userData);
  }
}

async function getCachedUser(userId) {
  const key = `user:${userId}`;
  
  try {
    if (global.redisClient) {
      const cached = await global.redisClient.get(key);
      if (cached) {
        return JSON.parse(cached);
      }
    } else {
      return getCache(key);
    }
  } catch (error) {
    logger.error('Error getting cached user data:', error);
  }
  
  return null;
}

async function cachePresence(userId, presenceData) {
  const key = `presence:${userId}`;
  
  try {
    if (global.redisClient) {
      await global.redisClient.setEx(key, CACHE_TTL / 1000, JSON.stringify(presenceData));
    } else {
      setCache(key, presenceData);
    }
    
    logger.debug(`Cached presence data for ${userId}`);
  } catch (error) {
    logger.error('Error caching presence data:', error);
    setCache(key, presenceData);
  }
}

async function getCachedPresence(userId) {
  const key = `presence:${userId}`;
  
  try {
    if (global.redisClient) {
      const cached = await global.redisClient.get(key);
      if (cached) {
        return JSON.parse(cached);
      }
    } else {
      return getCache(key);
    }
  } catch (error) {
    logger.error('Error getting cached presence data:', error);
  }
  
  return null;
}

async function invalidateUser(userId) {
  const userKey = `user:${userId}`;
  const presenceKey = `presence:${userId}`;
  
  try {
    if (global.redisClient) {
      await Promise.all([
        global.redisClient.del(userKey),
        global.redisClient.del(presenceKey)
      ]);
    } else {
      memoryCache.delete(userKey);
      memoryCache.delete(presenceKey);
    }
    
    logger.debug(`Invalidated cache for user ${userId}`);
  } catch (error) {
    logger.error('Error invalidating user cache:', error);
  }
}

function clearCache() {
  memoryCache.clear();
  logger.debug('Memory cache cleared');
}

// Clean up expired memory cache entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [key, value] of memoryCache.entries()) {
    if (now - value.timestamp > CACHE_TTL) {
      memoryCache.delete(key);
    }
  }
}, CACHE_TTL);

module.exports = {
  cacheUser,
  getCachedUser,
  cachePresence,
  getCachedPresence,
  invalidateUser,
  clearCache
};
