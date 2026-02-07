// 示例数据种子脚本
// 运行: npx ts-node --compiler-options '{"module":"CommonJS"}' scripts/seed.ts
// 或者: npx tsx scripts/seed.ts

import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 开始播种数据...')

  // 1. 创建测试用户
  const hashedPassword = await bcrypt.hash('password123', 10)
  
  const testUser = await prisma.user.upsert({
    where: { email: 'test@example.com' },
    update: {},
    create: {
      email: 'test@example.com',
      name: '测试用户',
      password: hashedPassword,
    },
  })
  console.log('✅ 创建测试用户:', testUser.email)

  // 2. 创建激活码
  const activationCodes = [
    { code: 'TRIAL-7DAY-FREE', plan: 'basic', durationDays: 7, maxUsers: 100 },
    { code: 'PRO-30DAY-2024', plan: 'pro', durationDays: 30, maxUsers: 50 },
    { code: 'VIP-90DAY-ELITE', plan: 'enterprise', durationDays: 90, maxUsers: 20 },
    { code: 'ANNUAL-365-GOLD', plan: 'enterprise', durationDays: 365, maxUsers: 10 },
  ]

  for (const codeData of activationCodes) {
    const code = await prisma.activationCode.upsert({
      where: { code: codeData.code },
      update: {},
      create: codeData,
    })
    console.log('✅ 创建激活码:', code.code)
  }

  // 3. 创建示例空投项目
  const airdrops = [
    {
      name: 'Arbitrum',
      slug: 'arbitrum',
      description: 'Arbitrum 是以太坊的 Layer 2 扩展解决方案，使用 Optimistic Rollups 技术提供快速、低成本的交易。',
      logo: 'https://cryptologos.cc/logos/arbitrum-arb-logo.png',
      website: 'https://arbitrum.io',
      twitter: 'https://twitter.com/arbitrum',
      discord: 'https://discord.gg/arbitrum',
      category: 'DeFi',
      status: 'ended',
      estimatedValue: '$1,000 - $10,000',
      difficulty: 'medium',
      tags: 'Layer2,Rollup,以太坊',
      tasks: JSON.stringify([
        '在 Arbitrum 上进行交易',
        '使用跨链桥转移资产',
        '参与 DeFi 协议',
      ]),
    },
    {
      name: 'LayerZero',
      slug: 'layerzero',
      description: 'LayerZero 是一个全链互操作协议，支持跨链消息传递。尚未发币，预计空投价值较高。',
      logo: 'https://assets.coingecko.com/coins/images/28206/large/layerzero.png',
      website: 'https://layerzero.network',
      twitter: 'https://twitter.com/LayerZero_Labs',
      discord: 'https://discord.gg/layerzero',
      category: 'Infrastructure',
      status: 'active',
      estimatedValue: '$500 - $5,000',
      difficulty: 'hard',
      tags: '跨链,基础设施,热门',
      tasks: JSON.stringify([
        '使用 Stargate 跨链',
        '在多链上使用 LayerZero 协议',
        '积累交易量和交易次数',
      ]),
    },
    {
      name: 'zkSync Era',
      slug: 'zksync-era',
      description: 'zkSync Era 是以太坊的 zk-Rollup 扩展方案，提供高效率和安全性。目前正在进行空投活动。',
      logo: 'https://assets.coingecko.com/coins/images/28597/large/zksync.png',
      website: 'https://zksync.io',
      twitter: 'https://twitter.com/zaborovskiy',
      discord: 'https://discord.gg/zksync',
      category: 'DeFi',
      status: 'active',
      estimatedValue: '$300 - $3,000',
      difficulty: 'easy',
      tags: 'Layer2,ZK-Rollup,以太坊',
      tasks: JSON.stringify([
        '桥接 ETH 到 zkSync Era',
        '使用 DEX 交易',
        '参与借贷协议',
        '部署智能合约',
      ]),
    },
    {
      name: 'Scroll',
      slug: 'scroll',
      description: 'Scroll 是一个原生的 zkEVM Layer 2 解决方案，与以太坊高度兼容。',
      logo: 'https://scroll.io/logo.png',
      website: 'https://scroll.io',
      twitter: 'https://twitter.com/Scroll_ZKP',
      discord: 'https://discord.gg/scroll',
      category: 'DeFi',
      status: 'upcoming',
      estimatedValue: '$200 - $2,000',
      difficulty: 'medium',
      tags: 'Layer2,zkEVM,新项目',
      tasks: JSON.stringify([
        '桥接资产到 Scroll',
        '使用生态系统 DApps',
        '持续交互',
      ]),
    },
    {
      name: 'Linea',
      slug: 'linea',
      description: 'Linea 是 ConsenSys 推出的 zkEVM Layer 2，由 MetaMask 团队开发。',
      logo: 'https://linea.build/logo.png',
      website: 'https://linea.build',
      twitter: 'https://twitter.com/LineaBuild',
      discord: 'https://discord.gg/linea',
      category: 'DeFi',
      status: 'active',
      estimatedValue: '$100 - $1,500',
      difficulty: 'easy',
      tags: 'Layer2,zkEVM,ConsenSys',
      tasks: JSON.stringify([
        '使用官方桥接资产',
        '参与 Linea 上的 DeFi',
        '完成官方任务',
      ]),
    },
    {
      name: 'Blast',
      slug: 'blast',
      description: 'Blast 是新兴的 Layer 2 项目，主打原生收益和高回报。由 Blur 团队创建。',
      logo: 'https://blast.io/logo.png',
      website: 'https://blast.io',
      twitter: 'https://twitter.com/blast',
      category: 'DeFi',
      status: 'active',
      estimatedValue: '$500 - $8,000',
      difficulty: 'medium',
      tags: 'Layer2,Blur,热门',
      tasks: JSON.stringify([
        '存入 ETH/USDB',
        '邀请好友',
        '积累 Blast Points',
      ]),
    },
    {
      name: 'Starknet',
      slug: 'starknet',
      description: 'Starknet 是基于 STARK 证明的 Layer 2 网络，专注于可扩展性。已发币但后续可能有更多空投。',
      logo: 'https://starknet.io/logo.png',
      website: 'https://starknet.io',
      twitter: 'https://twitter.com/Starknet',
      discord: 'https://discord.gg/starknet',
      category: 'DeFi',
      status: 'active',
      estimatedValue: '$200 - $1,000',
      difficulty: 'hard',
      tags: 'Layer2,STARK,已发币',
      tasks: JSON.stringify([
        '使用 Starknet 生态 DApps',
        '参与治理',
        '持续交互获取后续空投',
      ]),
    },
    {
      name: 'Base',
      slug: 'base',
      description: 'Base 是 Coinbase 推出的 Layer 2 网络，基于 OP Stack 构建。',
      logo: 'https://base.org/logo.png',
      website: 'https://base.org',
      twitter: 'https://twitter.com/BuildOnBase',
      discord: 'https://discord.gg/base',
      category: 'DeFi',
      status: 'active',
      estimatedValue: '$100 - $500',
      difficulty: 'easy',
      tags: 'Layer2,Coinbase,OP Stack',
      tasks: JSON.stringify([
        '桥接资产到 Base',
        '使用生态 DApps',
        '参与 Onchain Summer 活动',
      ]),
    },
  ]

  for (const airdropData of airdrops) {
    const airdrop = await prisma.airdrop.upsert({
      where: { slug: airdropData.slug },
      update: airdropData,
      create: airdropData,
    })
    console.log('✅ 创建空投项目:', airdrop.name)
  }

  // 4. 为测试用户创建订阅
  await prisma.subscription.upsert({
    where: { userId: testUser.id },
    update: {},
    create: {
      userId: testUser.id,
      plan: 'pro',
      status: 'active',
      expireDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30天后过期
    },
  })
  console.log('✅ 创建用户订阅')

  // 5. 创建用户偏好设置
  await prisma.userPreference.upsert({
    where: { userId: testUser.id },
    update: {},
    create: {
      userId: testUser.id,
      emailNotifications: true,
      browserNotifications: true,
      preferredCategories: 'DeFi,Layer2',
      difficultyFilter: 'all',
    },
  })
  console.log('✅ 创建用户偏好设置')

  console.log('')
  console.log('🎉 数据播种完成！')
  console.log('')
  console.log('📝 测试账号信息:')
  console.log('   邮箱: test@example.com')
  console.log('   密码: password123')
  console.log('')
  console.log('🔑 可用激活码:')
  activationCodes.forEach(c => {
    console.log(`   ${c.code} (${c.plan}, ${c.durationDays}天)`)
  })
}

main()
  .catch((e) => {
    console.error('❌ 播种失败:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
