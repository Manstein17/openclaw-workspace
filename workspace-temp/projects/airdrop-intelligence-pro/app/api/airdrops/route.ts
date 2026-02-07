import { NextResponse } from 'next/server'
import prisma from '@/lib/prisma'

// GET /api/airdrops - 获取空投列表
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    
    // 解析查询参数
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '20')
    const category = searchParams.get('category')
    const status = searchParams.get('status')
    const difficulty = searchParams.get('difficulty')
    const search = searchParams.get('search')

    // 构建查询条件
    const where: any = {}

    if (category) {
      where.category = category
    }

    if (status) {
      where.status = status
    } else {
      // 默认只显示即将开始和进行中的空投
      where.status = { in: ['upcoming', 'active'] }
    }

    if (difficulty) {
      where.difficulty = difficulty
    }

    if (search) {
      where.OR = [
        { name: { contains: search } },
        { description: { contains: search } },
        { tags: { contains: search } }
      ]
    }

    // 计算分页
    const skip = (page - 1) * limit

    // 查询数据
    const [airdrops, total] = await Promise.all([
      prisma.airdrop.findMany({
        where,
        orderBy: [
          { startDate: 'asc' },
          { createdAt: 'desc' }
        ],
        skip,
        take: limit
      }),
      prisma.airdrop.count({ where })
    ])

    // 返回分页数据
    return NextResponse.json({
      data: airdrops,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    })
  } catch (error) {
    console.error('获取空投列表错误:', error)
    return NextResponse.json(
      { error: '获取数据失败' },
      { status: 500 }
    )
  }
}

// POST /api/airdrops - 创建空投（管理员）
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const {
      name,
      description,
      category,
      status,
      startDate,
      endDate,
      website,
      twitter,
      discord,
      estimatedValue,
      difficulty,
      tags
    } = body

    // 验证必填字段
    if (!name) {
      return NextResponse.json(
        { error: '请提供空投名称' },
        { status: 400 }
      )
    }

    // 生成 slug
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')

    // 创建空投
    const airdrop = await prisma.airdrop.create({
      data: {
        name,
        slug,
        description,
        category: category || 'Other',
        status: status || 'upcoming',
        startDate: startDate ? new Date(startDate) : null,
        endDate: endDate ? new Date(endDate) : null,
        website,
        twitter,
        discord,
        estimatedValue,
        difficulty: difficulty || 'medium',
        tags: tags?.join(',')
      }
    })

    return NextResponse.json({
      message: '创建成功',
      airdrop
    })
  } catch (error) {
    console.error('创建空投错误:', error)
    return NextResponse.json(
      { error: '创建失败' },
      { status: 500 }
    )
  }
}
