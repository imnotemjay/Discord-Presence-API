const { Client, GatewayIntentBits, Presence } = require('discord.js');
const logger = require('../utils/logger');
const { cacheUser, cachePresence, getCachedPresence, getCachedUser } = require('../utils/cache');

class DiscordHandler {
  constructor() {
    this.client = null;
    this.io = null;
    this.ready = false;
  }

  async init(io) {
    this.io = io;
    
    // Setup Discord client with required intents
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildPresences,
        GatewayIntentBits.GuildMembers
      ]
    });

    this.client.once('ready', () => {
      this.ready = true;
      logger.info(`Bot logged in as ${this.client.user.tag}`);
      logger.info(`Bot is in ${this.client.guilds.cache.size} servers`);
    });

    // Handle presence updates
    this.client.on('presenceUpdate', async (oldPresence, newPresence) => {
      if (!newPresence || !newPresence.userId) return;
      
      try {
        const presenceData = this.formatPresence(newPresence);
        await cachePresence(newPresence.userId, presenceData);
        
        // Send update to subscribed clients
        this.io.to(`user_${newPresence.userId}`).emit('presenceUpdate', {
          userId: newPresence.userId,
          ...presenceData,
          timestamp: Date.now()
        });
        
        logger.debug(`Updated presence for user ${newPresence.userId}`);
      } catch (error) {
        logger.error('Error handling presence update:', error);
      }
    });

    this.client.on('userUpdate', async (oldUser, newUser) => {
      if (!newUser) return;
      
      try {
        const userData = this.formatUser(newUser);
        await cacheUser(newUser.id, userData);
        
        // Broadcast to WebSocket subscribers
        this.io.to(`user_${newUser.id}`).emit('userUpdate', {
          userId: newUser.id,
          ...userData,
          timestamp: Date.now()
        });
        
        logger.debug(`User updated: ${newUser.tag}`);
      } catch (error) {
        logger.error('Error handling user update:', error);
      }
    });

    this.client.on('error', (error) => {
      logger.error('Discord client error:', error);
    });

    this.client.on('disconnect', () => {
      this.ready = false;
      logger.warn('Discord client disconnected');
    });

    await this.client.login(process.env.DISCORD_BOT_TOKEN);
  }

  formatUser(user) {
    return {
      id: user.id,
      username: user.username,
      displayName: user.displayName,
      avatar: user.avatar ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png` : null,
      discriminator: user.discriminator,
      publicFlags: user.publicFlags,
      banner: user.banner ? `https://cdn.discordapp.com/banners/${user.id}/${user.banner}.png` : null,
      bannerColor: user.hexAccentColor || null,
      accentColor: user.hexAccentColor || null,
      avatarDecoration: user.avatarDecorationData?.asset || null,
      premiumType: user.premiumType,
      verified: user.verified,
      createdAt: user.createdAt.toISOString()
    };
  }

  formatPresence(presence) {
    const activities = presence.activities.map(activity => ({
      name: activity.name,
      type: activity.type,
      details: activity.details || null,
      state: activity.state || null,
      applicationId: activity.applicationId || null,
      assets: activity.assets ? {
        largeImage: activity.assets.largeImage ? 
          `https://cdn.discordapp.com/app-assets/${activity.applicationId}/${activity.assets.largeImage}.png` : null,
        largeText: activity.assets.largeText || null,
        smallImage: activity.assets.smallImage ? 
          `https://cdn.discordapp.com/app-assets/${activity.applicationId}/${activity.assets.smallImage}.png` : null,
        smallText: activity.assets.smallText || null
      } : null,
      timestamps: activity.timestamps ? {
        start: activity.timestamps.start || null,
        end: activity.timestamps.end || null
      } : null
    }));

    return {
      userId: presence.userId,
      status: presence.status,
      activities,
      lastSeen: Date.now(),
      guildId: presence.guild?.id || null
    };
  }

  async getUser(userId) {
    if (!this.ready) {
      throw new Error('Discord client not ready');
    }

    try {
      // Try to get from cache first
      const cachedUser = await getCachedUser(userId);
      if (cachedUser) return cachedUser;

      // Fetch from Discord API
      const user = await this.client.users.fetch(userId);
      const formattedUser = this.formatUser(user);
      await cacheUser(userId, formattedUser);
      return formattedUser;
    } catch (error) {
      logger.error(`Error fetching user ${userId}:`, error);
      throw error;
    }
  }

  async getPresence(userId, guildId = null) {
    if (!this.ready) {
      throw new Error('Discord client not ready');
    }

    try {
      // Try to get from cache first
      const cachedPresence = await getCachedPresence(userId);
      if (cachedPresence) return cachedPresence;

      // If guildId is provided, try to get guild-specific presence
      if (guildId) {
        const guild = this.client.guilds.cache.get(guildId);
        if (guild) {
          const member = await guild.members.fetch(userId).catch(() => null);
          if (member && member.presence) {
            const presenceData = this.formatPresence(member.presence);
            await cachePresence(userId, presenceData);
            return presenceData;
          }
        }
      }

      // Fallback to general presence
      const presence = this.client.presences.cache.get(userId);
      if (presence) {
        const presenceData = this.formatPresence(presence);
        await cachePresence(userId, presenceData);
        return presenceData;
      }

      // Return offline presence if not found
      return {
        userId,
        status: 'offline',
        activities: [],
        lastSeen: null,
        guildId
      };
    } catch (error) {
      logger.error(`Error fetching presence for user ${userId}:`, error);
      throw error;
    }
  }

  isConnected() {
    return this.ready && this.client && this.client.ws.status === 0;
  }

  destroy() {
    if (this.client) {
      this.client.destroy();
    }
  }
}

module.exports = new DiscordHandler();
