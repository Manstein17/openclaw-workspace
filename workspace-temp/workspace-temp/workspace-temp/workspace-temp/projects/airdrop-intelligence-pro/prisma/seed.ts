import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 开始数据库 seeding...')

  // 创建测试用户
  const user = await prisma.user.upsert({
    where: { email: 'test@example.com' },
    update: {},
    create: {
      email: 'test@example.com',
      name: '测试用户',
      password: '$2a$10$dummyPasswordHash', // mock hash
      preferences: {
        create: {
          emailNotifications: true,
          browserNotifications: false,
          difficultyFilter: 'all'
        }
      }
    }
  })
  console.log('✅ 测试用户创建成功:', user.email)

  // 创建免费订阅
  const subscription = await prisma.subscription.upsert({
    where: { userId: user.id },
    update: {},
    create: {
      userId: user.id,
      plan: 'free',
      status: 'active'
    }
  })
  console.log('✅ 订阅创建成功:', subscription.plan)

  // 创建激活码
  const activationCode = await prisma.activationCode.upsert({
    where: { code: 'PRO-2024-FREE' },
    update: {},
    create: {
      code: 'PRO-2024-FREE',
      plan: 'pro',
      durationDays: 30,
      maxUsers: 100,
      usedCount: 0,
      isActive: true
    }
  })
  console.log('✅ 激活码创建成功:', activationCode.code)

  // 创建示例空投项目
  const airdrops = [
    {
      name: 'ZetaChain',
      slug: 'zetachain',
      description: 'ZetaChain 是第一个连接所有区块链的 L1 区块链，提供安全的跨链消息传递和流动性。',
      category: 'Infrastructure',
      status: 'active',
      difficulty: 'medium',
      estimatedValue: '$500-$2,000',
      website: 'https://zetachain.com',
      twitter: 'https://twitter.com/ZetaChain',
      discord: 'https://discord.gg/zetachain',
      tasks: JSON.stringify([
        { name: '桥接资产到 ZetaChain', status: 'required', difficulty: 'easy' },
        { name: '添加流动性到 Pools', status: 'required', difficulty: 'medium' },
        { name: '进行 Swap 交易', status: 'required', difficulty: 'easy' },
        { name: 'mint ZRC-20 代币', status: 'required', difficulty: 'easy' }
      ])
    },
    {
      name: 'LayerZero',
      slug: 'layerzero',
      description: 'LayerZero 是一个全链互操作性协议，支持跨链消息传递和资产转移。',
      category: 'Infrastructure',
      status: 'active',
      difficulty: 'hard',
      estimatedValue: '$1,000-$5,000',
      website: 'https://layerzero.network',
      twitter: 'https://twitter.com/LayerZero_Labs',
      tasks: JSON.stringify([
        { name: '使用 Stargate Bridge', status: 'required', difficulty: 'medium' },
        { name: '进行跨链 Swap', status: 'required', difficulty: 'medium' },
        { name: '提供流动性', status: 'required', difficulty: 'hard' },
        { name: '参与治理投票', status: 'optional', difficulty: 'medium' }
      ])
    },
    {
      name: 'Starknet',
      slug: 'starknet',
      description: 'Starknet 是一个基于 ZK Rollup 的 L2 扩展解决方案，支持以太坊智能合约。',
      category: 'Infrastructure',
      status: 'active',
      difficulty: 'medium',
      estimatedValue: '$200-$1,000',
      website: 'https://starknet.io',
      twitter: 'https://twitter.com/Starknet',
      tasks: JSON.stringify([
        { name: '在主网进行交易', status: 'required', difficulty: 'easy' },
        { name: '使用 dApps', status: 'required', difficulty: 'easy' },
        { name: 'mint NFT', status: 'optional', difficulty: 'easy' }
      ])
    },
    {
      name: 'Scroll',
      slug: 'scroll',
      description: 'Scroll 是一个基于 ZK Rollup 的以太坊 L2 扩展方案。',
      category: 'Infrastructure',
      status: 'active',
      difficulty: 'easy',
      estimatedValue: '$100-$500',
      website: 'https://scroll.io',
      twitter: 'https://twitter.com/Scroll_ZK',
      tasks: JSON.stringify([
        { name: '桥接到 Scroll', status: 'required', difficulty: 'easy' },
        { name: '进行 Swap 交易', status: 'required', difficulty: 'easy' },
        { name: '提供流动性', status: 'optional', difficulty: 'medium' }
      ])
    },
    {
      name: 'zkSync',
      slug: 'zksync',
      description: 'zkSync Era 是一个基于 ZK Rollup 的以太坊 L2，提供低费用和高安全性。',
      category: 'Infrastructure',
      status: 'upcoming',
      difficulty: 'medium',
      estimatedValue: '$500-$3,000',
      website: 'https://zksync.io',
      twitter: 'https://twitter.com/zksync',
      tasks: JSON.stringify([
        { name: '在 Era 主网交易', status: 'required', difficulty: 'medium' },
        { name: '使用原生桥接', status: 'required', difficulty: 'easy' },
        { name: '部署智能合约', status: 'optional', difficulty: 'hard' }
      ])
    },
    {
      name: 'Blast',
      slug: 'blast',
      description: 'Blast 是一个带有原生收益的以太坊 L2 扩展方案。',
      category: 'Infrastructure',
      status: 'active',
      difficulty: 'medium',
      estimatedValue: '$200-$1,500',
      website: 'https://blast.io',
      twitter: 'https://twitter.com/Blast_L2',
      tasks: JSON.stringify([
        { name: '桥接 ETH 到 Blast', status: 'required', difficulty: 'easy' },
        { name: '存入 DApps', status: 'required', difficulty: 'medium' },
        { name: '进行 Blip 投票', status: 'optional', difficulty: 'easy' }
      ])
    },
    {
      name: 'MetaMask',
      slug: 'metamask',
      description: 'MetaMask 正在探索代币发行，可能会有空投给早期用户。',
      category: 'Wallet',
      status: 'upcoming',
      difficulty: 'easy',
      estimatedValue: '$100-$500',
      website: 'https://metamask.io',
      twitter: 'https://twitter.com/MetaMask',
      tasks: JSON.stringify([
        { name: '使用 MetaMask Swap', status: 'required', difficulty: 'easy' },
        { name: '使用 Bridge 功能', status: 'required', difficulty: 'easy' },
        { name: '使用 MetaMask Snaps', status: 'optional', difficulty: 'medium' }
      ])
    },
    {
      name: 'Berachain',
      slug: 'berachain',
      description: 'Berachain 是一个基于 Proof of Liquidity 的高性能 L1 区块链。',
      category: 'Infrastructure',
      status: 'upcoming',
      difficulty: 'medium',
      estimatedValue: '$1,000-$5,000',
      website: 'https://berachain.com',
      twitter: 'https://twitter.com/berachain',
      tasks: JSON.stringify([
        { name: '参与测试网活动', status: 'required', difficulty: 'medium' },
        { name: '提供流动性', status: 'required', difficulty: 'medium' },
        { name: '参与社区治理', status: 'optional', difficulty: 'easy' }
      ])
    }
  ]

  for (const airdrop of airdrops) {
    const existing = await prisma.airdrop.findUnique({
      where: { slug: airdrop.slug }
    })
    
    if (!existing) {
      await prisma.airdrop.create({ data: airdrop })
      console.log(`✅ 空投创建成功: ${airdrop.name}`)
    } else {
      console.log(`⏭️ 空投已存在: ${airdrop.name}`)
    }
  }

  console.log('🎉 数据库 seeding 完成!')
}

main()
  .catch((e) => {
    console.error('❌ Seeding 失败:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
