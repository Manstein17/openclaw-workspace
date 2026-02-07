/**
 * Airdrop Search Script
 * 使用 Brave API 全网搜索空投信息
 */

const axios = require('axios');
const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const path = require('path');

// 配置
const config = {
  braveApiKey: process.env.BRAVE_API_KEY || '',
  logFile: path.join(__dirname, '..', '..', '..', '..', 'logs', 'airdrop-search.log'),
  // 搜索关键词
  searchQueries: [
    'crypto airdrop 2024',
    'testnet airdrop opportunity',
    'new token launch airdrop',
    '区块链空投 2024',
    'Layer2 airdrop announcement',
    'DeFi protocol airdrop',
    'NFT airdrop free mint',
    'Web3 project token distribution'
  ],
  // 已知的热门空投项目
  knownProjects: [
    { name: 'ZetaChain', category: 'Layer1' },
    { name: 'LayerZero', category: 'Cross-chain' },
    { name: 'Scroll', category: 'Layer2' },
    { name: 'Linea', category: 'Layer2' },
    { name: 'Starknet', category: 'Layer2' },
    { name: 'Arbitrum', category: 'Layer2' },
    { name: 'Optimism', category: 'Layer2' },
    { name: 'Metis', category: 'Layer2' },
    { name: 'zkSync', category: 'Layer2' },
    { name: 'Blast', category: 'Layer2' },
    { name: 'EigenLayer', category: 'Restaking' },
    { name: 'AltLayer', category: 'Layer2' },
    { name: 'Mantle', category: 'Layer2' },
    { name: 'Base', category: 'Layer2' },
    { name: 'Taiko', category: 'Layer2' },
    { name: 'Polygon zkEVM', category: 'Layer2' },
    { name: 'Filecoin', category: 'Storage' },
    { name: 'Arweave', category: 'Storage' },
    { name: 'Aleo', category: 'Privacy' },
    { name: 'Aztec', category: 'Privacy' },
    { name: 'Mina', category: 'Layer1' },
    { name: 'Sui', category: 'Layer1' },
    { name: 'Aptos', category: 'Layer1' },
    { name: 'Sei', category: 'Layer1' }
  ]
};

const prisma = new PrismaClient();

// 日志函数
function log(message, type = 'INFO') {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${type}] ${message}`;
  console.log(logMessage);
  
  // 确保日志目录存在
  const logDir = path.dirname(config.logFile);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  fs.appendFileSync(config.logFile, logMessage + '\n');
}

// 使用 Brave API 搜索
async function braveSearch(query) {
  if (!config.braveApiKey) {
    log(`未配置 Brave API Key，跳过搜索: ${query}`, 'WARN');
    return null;
  }

  try {
    const response = await axios.get('https://api.search.brave.com/res/v1/web/search', {
      params: {
        q: query,
        count: 10,
        country: 'US',
        search_lang: 'en'
      },
      headers: {
        'Accept': 'application/json',
        'X-Subscription-Token': config.braveApiKey
      }
    });

    return response.data;
  } catch (error) {
    log(`Brave 搜索失败: ${error.message}`, 'ERROR');
    return null;
  }
}

// 解析搜索结果并提取空投信息
function parseSearchResults(results, query) {
  if (!results || !results.webResults) return [];

  const airdrops = [];

  for (const result of results.webResults) {
    // 过滤不相关的结果
    if (!result.url || !result.title) continue;
    
    // 排除已知的不相关网站
    const excludeDomains = ['twitter.com', 'x.com', 'telegram.org', 'discord.com'];
    if (excludeDomains.some(domain => result.url.includes(domain))) continue;

    // 提取项目名称（简化处理：从标题中提取）
    const title = result.title || '';
    const description = result.description || '';
    
    // 检查是否包含空投相关信息
    const hasAirdropKeywords = /airdrop|token|launch|分发|空投/i.test(title + description);
    
    if (hasAirdropKeywords) {
      airdrops.push({
        title,
        url: result.url,
        description: description.substring(0, 300),
        source: 'brave-search',
        query
      });
    }
  }

  return airdrops;
}

// 保存空投信息到数据库
async function saveAirdropFromSearch(airdropData) {
  try {
    // 检查是否已存在
    const existing = await prisma.airdrop.findFirst({
      where: {
        OR: [
          { name: { contains: airdropData.title.split('|')[0].trim(), mode: 'insensitive' } },
          { website: airdropData.url }
        ]
      }
    });

    if (existing) {
      log(`已存在: ${existing.name}`, 'SKIP');
      return null;
    }

    // 创建新记录
    const airdrop = await prisma.airdrop.create({
      data: {
        name: airdropData.title.split('|')[0].trim().substring(0, 100),
        description: airdropData.description,
        category: detectCategory(airdropData.title + airdropData.description),
        status: 'pending',
        difficulty: 'medium',
        source: 'web-search',
        sourceUrl: airdropData.url,
        website: airdropData.url,
        estimatedValue: null,
        startDate: new Date(),
        instructions: JSON.stringify([{
          type: 'search',
          query: airdropData.query,
          date: new Date().toISOString()
        }]),
        createdAt: new Date(),
        updatedAt: new Date()
      }
    });

    log(`✅ 新发现: ${airdrop.name}`, 'SUCCESS');
    return airdrop;
  } catch (error) {
    log(`保存失败: ${error.message}`, 'ERROR');
    return null;
  }
}

// 检测项目分类
function detectCategory(text) {
  const categories = {
    'Layer2': /layer2|l2|rollup|zk|\bop\b|optimism|arbitrum|zkevm/i,
    'Layer1': /layer1|l1|blockchain|mainnet/i,
    'Cross-chain': /cross.?chain|bridge|interoperability/i,
    'DEX': /dex|exchange|swap|decentralized/i,
    'DeFi': /defi|finance|yield|farming|lending/i,
    'NFT': /nft|collection|mint|艺术品/i,
    'Gaming': /game|gaming|play.?to.?earn|metaverse/i,
    'Privacy': /privacy|zero.?knowledge|zk-snark/i,
    'Storage': /storage|file| decentrali.*storage/i,
    'Restaking': /restake|restaking|re质押/i
  };

  for (const [category, pattern] of Object.entries(categories)) {
    if (pattern.test(text)) return category;
  }

  return 'Other';
}

// 检查已知项目的最新状态
async function checkKnownProjects() {
  log('📊 检查已知空投项目状态...');
  
  for (const project of config.knownProjects) {
    try {
      // 检查项目是否已在数据库中
      const existing = await prisma.airdrop.findFirst({
        where: { name: { contains: project.name, mode: 'insensitive' } }
      });

      if (!existing) {
        // 添加新项目
        await prisma.airdrop.create({
          data: {
            name: project.name,
            description: `Known airdrop project - ${project.category}`,
            category: project.category,
            status: 'pending',
            difficulty: 'medium',
            source: 'known-projects-list',
            estimatedValue: detectEstimatedValue(project.category),
            instructions: JSON.stringify([{
              type: 'known-project',
              note: '从已知空投项目列表添加'
            }]),
            createdAt: new Date(),
            updatedAt: new Date()
          }
        });
        log(`✅ 添加已知项目: ${project.name}`, 'ADD');
      }
    } catch (error) {
      log(`处理项目 ${project.name} 失败: ${error.message}`, 'ERROR');
    }
  }
}

// 根据分类估算空投价值
function detectEstimatedValue(category) {
  const values = {
    'Layer1': '$1000-5000',
    'Layer2': '$500-3000',
    'Cross-chain': '$500-2000',
    'DEX': '$100-500',
    'DeFi': '$100-500',
    'NFT': '$50-200',
    'Gaming': '$50-300',
    'Other': '$100-500'
  };
  return values[category] || values['Other'];
}

// 主搜索函数
async function performSearch() {
  log('🚀 开始全网空投搜索...');
  const foundAirdrops = [];

  // 1. 搜索网络结果
  for (const query of config.searchQueries) {
    log(`📝 搜索: "${query}"`);
    const results = await braveSearch(query);
    
    if (results) {
      const parsed = parseSearchResults(results, query);
      foundAirdrops.push(...parsed);
      log(`   找到 ${parsed.length} 条相关结果`);
    }
    
    // 避免请求过快
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // 2. 保存搜索结果
  log('💾 保存搜索到的空投...');
  let savedCount = 0;
  for (const airdrop of foundAirdrops) {
    const saved = await saveAirdropFromSearch(airdrop);
    if (saved) savedCount++;
  }

  // 3. 检查已知项目
  await checkKnownProjects();

  // 输出统计
  const result = { found: foundAirdrops.length, saved: savedCount };
  log('📈 搜索完成统计:', 'INFO');
  log(`   - 网络搜索结果: ${result.found}`, 'INFO');
  log(`   - 保存到数据库: ${result.saved}`, 'INFO');

  return result;
}

// 主动搜索特定项目
async function searchSpecificProject(projectName) {
  log(`🔍 搜索特定项目: ${projectName}`);
  
  const queries = [
    `${projectName} airdrop announcement`,
    `${projectName} token launch`,
    `${projectName} testnet incentive`
  ];

  for (const query of queries) {
    const results = await braveSearch(query);
    if (results) {
      const parsed = parseSearchResults(results, query);
      for (const airdrop of parsed) {
        await saveAirdropFromSearch(airdrop);
      }
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
}

// 主入口
async function main() {
  try {
    const startTime = Date.now();
    
    const { found, saved } = await performSearch();
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    
    log('='.repeat(50), 'INFO');
    log(`🎉 空投搜索完成! 用时: ${duration}秒`, 'INFO');
    log(`📊 本次搜索发现: ${found} 条结果, 保存: ${saved} 个新空投`, 'INFO');
    log('='.repeat(50), 'INFO');

    // 输出发现的新空投列表
    if (saved > 0) {
      const newAirdrops = await prisma.airdrop.findMany({
        where: {
          createdAt: { gte: new Date(Date.now() - 60 * 60 * 1000) } // 最近1小时
        },
        orderBy: { createdAt: 'desc' },
        take: 10
      });

      log('\n🎁 新发现的空投:', 'INFO');
      for (const a of newAirdrops) {
        log(`   - ${a.name} (${a.category})`, 'INFO');
      }
    }

  } catch (error) {
    log(`搜索过程出错: ${error.message}`, 'FATAL');
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

// 如果直接运行
if (require.main === module) {
  main();
}

module.exports = { performSearch, searchSpecificProject, checkKnownProjects };
