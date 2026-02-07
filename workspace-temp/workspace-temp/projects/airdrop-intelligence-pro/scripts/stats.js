/**
 * 数据库统计脚本
 * 用于快速查看空投监控数据统计
 */

const { PrismaClient } = require('@prisma/client')
const fs = require('fs')
const path = require('path')

const prisma = new PrismaClient()

async function main() {
  console.log('📊 空投数据库统计')
  console.log('='.repeat(50))

  try {
    // 基本统计
    const total = await prisma.airdrop.count()
    const active = await prisma.airdrop.count({ where: { status: 'active' } })
    const pending = await prisma.airdrop.count({ where: { status: 'pending' } })
    const completed = await prisma.airdrop.count({ where: { status: 'completed' } })

    console.log(`\n📈 空投统计:`)
    console.log(`  总数: ${total}`)
    console.log(`  进行中: ${active}`)
    console.log(`  待确认: ${pending}`)
    console.log(`  已完成: ${completed}`)

    // 分类统计
    console.log(`\n📂 分类分布:`)
    const categories = await prisma.airdrop.groupBy({
      by: ['category'],
      _count: true,
      orderBy: { _count: { category: 'desc' } }
    })

    categories.forEach(cat => {
      console.log(`  ${cat.category}: ${cat._count}`)
    })

    // 来源统计
    console.log(`\n🔗 来源统计:`)
    const sources = await prisma.airdrop.groupBy({
      by: ['source'],
      _count: true
    })

    sources.forEach(source => {
      console.log(`  ${source.source || '未知'}: ${source._count}`)
    })

    // 最近添加
    console.log(`\n🕐 最近添加的空投:`)
    const recent = await prisma.airdrop.findMany({
      take: 5,
      orderBy: { createdAt: 'desc' },
      select: { name: true, category: true, status: true, createdAt: true }
    })

    recent.forEach(item => {
      console.log(`  - ${item.name} (${item.category}) - ${item.status}`)
    })

    console.log('\n' + '='.repeat(50))
    console.log('✅ 统计完成')

  } catch (error) {
    console.error('统计失败:', error.message)
  } finally {
    await prisma.$disconnect()
  }
}

main()
