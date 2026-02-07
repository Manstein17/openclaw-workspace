/**
 * Discord Airdrop Monitor
 * Monitors Discord channels for airdrop opportunities
 * 
 * Usage: node scripts/discord-airdrop-monitor.js
 */

const { Client, GatewayIntentBits, Events, EmbedBuilder } = require('discord.js');
const { PrismaClient } = require('@prisma/client');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const prisma = new PrismaClient();

// Configuration
const CONFIG = {
  // Keywords to detect airdrop opportunities
  AIRDROP_KEYWORDS: [
    'airdrop', 'token', 'claim', 'free token', 'giveaway', 
    'testnet', 'snapshot', 'eligibility', 'whitelist',
    'distribution', 'mint', '铸造',
    '代币', '空投', '快照', '领取', '激励计划', 'launch', '发行'
  ],
  
  // Popular airdrop project Discord servers
  MONITORED_SERVERS: [
    { name: 'LayerZero', id: '937479220046266419' },
    { name: 'Arbitrum', id: '585506313513435136' },
    { name: 'Optimism', id: '539639586829307916' },
    { name: 'ZkSync', id: '497112001428410369' },
    { name: 'StarkNet', id: '755479659274655836' },
    { name: 'Metamask', id: '542745027560353792' },
    { name: 'Uniswap', id: '597996664680628225' },
    { name: 'Blur', id: '894727359593816105' },
    { name: 'Magic Eden', id: '834976233792342026' },
    { name: 'Yuga Labs', id: '553326497783988747' },
    { name: 'ZetaChain', id: '894727359593816105' },
    { name: 'Scroll', id: '1031692686888558592' },
    { name: 'Linea', id: '1031692686888558592' }
  ],
  
  // Channels to ignore
  IGNORED_CHANNELS: ['bot-commands', 'off-topic', 'rules', 'announcements', 'welcome'],
  
  // Cooldown between duplicate detections (in hours)
  DUPLICATE_COOLDOWN_HOURS: 24
};

// Logging utility
const logger = {
  info: (message) => console.log(`[INFO] ${new Date().toISOString()} - ${message}`),
  warn: (message) => console.warn(`[WARN] ${new Date().toISOString()} - ${message}`),
  error: (message) => console.error(`[ERROR] ${new Date().toISOString()} - ${message}`),
  success: (message) => console.log(`[SUCCESS] ${new Date().toISOString()} - ${message}`)
};

// Initialize Discord client
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

/**
 * Check if message contains airdrop keywords
 */
function containsAirdropKeywords(message) {
  const content = message.toLowerCase();
  return CONFIG.AIRDROP_KEYWORDS.some(keyword => content.includes(keyword.toLowerCase()));
}

/**
 * Extract potential airdrop info from message
 */
function extractAirdropInfo(message, matchedKeywords) {
  // Extract URLs
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const urls = message.content.match(urlRegex) || [];
  
  // Extract potential project names
  const projectNameRegex = /([A-Z][a-z]+(?:[A-Z0-9][a-z0-9]*)+)/g;
  const projectNames = message.content.match(projectNameRegex) || [];
  
  // Extract dates
  const dateRegex = /(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})|(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})/gi;
  const dates = message.content.match(dateRegex) || [];
  
  return {
    content: message.content,
    urls: urls,
    projectNames: [...new Set(projectNames)],
    dates: dates,
    channel: message.channel.name,
    guild: message.guild?.name || 'Unknown',
    matchedKeywords: matchedKeywords,
    messageId: message.id,
    messageUrl: message.url,
    timestamp: message.createdAt
  };
}

/**
 * Save airdrop to database
 */
async function saveAirdropToDatabase(airdropInfo) {
  try {
    // Check for duplicates
    const existingAirdrop = await prisma.airdrop.findFirst({
      where: {
        OR: [
          { name: { contains: airdropInfo.projectNames[0] || '' } },
          { discord: airdropInfo.messageUrl }
        ],
        createdAt: {
          gte: new Date(Date.now() - CONFIG.DUPLICATE_COOLDOWN_HOURS * 60 * 60 * 1000)
        }
      }
    });
    
    if (existingAirdrop) {
      logger.info(`Duplicate detected, skipping: ${existingAirdrop.name}`);
      return null;
    }
    
    // Determine category based on keywords
    let category = 'General';
    const content = airdropInfo.content.toLowerCase();
    if (content.includes('testnet')) category = 'Testnet';
    else if (content.includes('nft')) category = 'NFT';
    else if (content.includes('game')) category = 'GameFi';
    else if (content.includes('defi') || content.includes('swap') || content.includes('liquidity')) category = 'DeFi';
    
    // Create slug from project name
    const slug = (airdropInfo.projectNames[0] || `discord-${Date.now()}`).toLowerCase().replace(/[^a-z0-9]+/g, '-');
    
    const airdrop = await prisma.airdrop.create({
      data: {
        name: airdropInfo.projectNames[0] || `Discord Airdrop ${new Date().toISOString().split('T')[0]}`,
        slug: `${slug}-${Date.now().toString(36)}`,
        description: airdropInfo.content.substring(0, 500),
        discord: airdropInfo.messageUrl,
        category: category,
        status: 'active',
        difficulty: 'medium',
        source: 'discord',
        tags: airdropInfo.matchedKeywords.join(', '),
        website: airdropInfo.urls.find(u => u.includes('http')) || null
      }
    });
    
    logger.success(`Saved new airdrop: ${airdrop.name} (ID: ${airdrop.id})`);
    return airdrop;
    
  } catch (error) {
    logger.error(`Failed to save airdrop: ${error.message}`);
    return null;
  }
}

/**
 * Send notification via webhook
 */
async function sendNotification(airdrop) {
  if (!process.env.DISCORD_WEBHOOK_URL) return;
  
  try {
    const { WebhookClient } = require('discord.js');
    const webhook = new WebhookClient({ url: process.env.DISCORD_WEBHOOK_URL });
    
    const embed = new EmbedBuilder()
      .setTitle('🎁 New Airdrop Detected!')
      .setDescription(airdrop.description?.substring(0, 500) || 'No description')
      .addFields(
        { name: 'Project', value: airdrop.name, inline: true },
        { name: 'Category', value: airdrop.category, inline: true },
        { name: 'Status', value: airdrop.status, inline: true },
        { name: 'Source', value: 'Discord', inline: true }
      )
      .setColor(0x00ff00)
      .setTimestamp();
    
    if (airdrop.website) embed.setURL(airdrop.website);
    
    await webhook.send({ embeds: [embed] });
    logger.info('Notification sent via webhook');
  } catch (error) {
    logger.warn(`Failed to send notification: ${error.message}`);
  }
}

/**
 * Process incoming message
 */
async function processMessage(message) {
  try {
    // Skip if message is from a bot
    if (message.author.bot) return;
    
    // Skip if in ignored channels
    if (CONFIG.IGNORED_CHANNELS.some(ignored => message.channel.name?.includes(ignored))) return;
    
    // Check for airdrop keywords
    if (!containsAirdropKeywords(message.content)) return;
    
    logger.info(`Detected potential airdrop in #${message.channel.name} (${message.guild?.name})`);
    
    // Find matched keywords
    const matchedKeywords = CONFIG.AIRDROP_KEYWORDS.filter(keyword => 
      message.content.toLowerCase().includes(keyword.toLowerCase())
    );
    
    // Extract info and save
    const airdropInfo = extractAirdropInfo(message, matchedKeywords);
    const saved = await saveAirdropToDatabase(airdropInfo);
    
    if (saved) {
      await sendNotification(saved);
    }
    
  } catch (error) {
    logger.error(`Error processing message: ${error.message}`);
  }
}

/**
 * Handle new message events
 */
client.on(Events.MessageCreate, async (message) => {
  await processMessage(message);
});

/**
 * Handle ready event
 */
client.on(Events.ClientReady, () => {
  logger.success(`Logged in as ${client.user.tag}`);
  logger.info(`Monitoring ${CONFIG.MONITORED_SERVERS.length} servers for airdrops...`);
  logger.info(`Airdrop keywords: ${CONFIG.AIRDROP_KEYWORDS.join(', ')}`);
});

/**
 * Error handling
 */
client.on(Events.Error, (error) => {
  logger.error(`Discord client error: ${error.message}`);
});

/**
 * Graceful shutdown
 */
async function shutdown() {
  logger.info('Shutting down Discord monitor...');
  try {
    if (client && client.destroy) {
      await client.destroy();
    }
    await prisma.$disconnect();
    logger.info('Shutdown complete');
    process.exit(0);
  } catch (error) {
    logger.error(`Error during shutdown: ${error.message}`);
    process.exit(1);
  }
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

/**
 * Main entry point
 */
async function main() {
  try {
    // Check for Discord token
    const discordToken = process.env.DISCORD_BOT_TOKEN;
    if (!discordToken) {
      logger.warn('DISCORD_BOT_TOKEN not found in .env file');
      logger.info('Running in simulation mode...');
      await runSimulationMode();
      return;
    }
    
    // Connect to database
    await prisma.$connect();
    logger.info('Connected to database');
    
    // Start Discord client
    await client.login(discordToken);
    
    logger.info('Discord Airdrop Monitor started successfully');
    
  } catch (error) {
    logger.error(`Failed to start Discord monitor: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Simulation mode for testing
 */
async function runSimulationMode() {
  logger.info('📡 Running in simulation mode...');
  
  await prisma.$connect();
  
  const mockAirdrops = [
    {
      name: 'Simulated - Zeko Network',
      description: 'Zero-knowledge Layer2 network launching incentive testnet soon',
      category: 'Layer2',
      status: 'active',
      difficulty: 'medium'
    },
    {
      name: 'Simulated - Lighter DEX',
      description: 'Zero-Gas DEX with multi-stage points system launching',
      category: 'DEX',
      status: 'active',
      difficulty: 'easy'
    }
  ];
  
  for (const airdrop of mockAirdrops) {
    try {
      const saved = await prisma.airdrop.create({
        data: {
          ...airdrop,
          slug: `${airdrop.name.toLowerCase().replace(/\s+/g, '-')}-sim-${Date.now()}`,
          source: 'simulated-monitor',
          discord: null,
          website: null
        }
      });
      logger.success(`Simulated airdrop: ${saved.name}`);
    } catch (error) {
      logger.error(`Simulation error: ${error.message}`);
    }
  }
  
  logger.info('Simulation complete');
  await shutdown();
}

// Export for testing
module.exports = {
  client,
  processMessage,
  extractAirdropInfo,
  containsAirdropKeywords,
  saveAirdropToDatabase,
  CONFIG
};

// Run if executed directly
if (require.main === module) {
  main();
}
