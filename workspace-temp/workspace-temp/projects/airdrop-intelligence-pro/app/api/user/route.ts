import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import prisma from '@/lib/prisma'

// GET /api/user - 获取当前用户信息
export async function GET() {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: '未登录' },
        { status: 401 }
      )
    }

    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
      select: {
        id: true,
        email: true,
        name: true,
        avatar: true,
        createdAt: true,
        subscription: {
          select: {
            plan: true,
            status: true,
            startDate: true,
            expireDate: true,
          }
        },
        preferences: {
          select: {
            emailNotifications: true,
            browserNotifications: true,
            difficultyFilter: true,
            preferredCategories: true,
          }
        }
      }
    })

    if (!user) {
      return NextResponse.json(
        { error: '用户不存在' },
        { status: 404 }
      )
    }

    return NextResponse.json({ user })
  } catch (error) {
    console.error('获取用户信息错误:', error)
    return NextResponse.json(
      { error: '获取用户信息失败' },
      { status: 500 }
    )
  }
}

// PATCH /api/user - 更新用户信息
export async function PATCH(request: Request) {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: '未登录' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const { name, avatar, preferences } = body

    // 更新用户基本信息
    if (name) {
      await prisma.user.update({
        where: { id: session.user.id },
        data: { name }
      })
    }

    // 更新用户偏好设置
    if (preferences) {
      await prisma.userPreference.upsert({
        where: { userId: session.user.id },
        update: preferences,
        create: {
          userId: session.user.id,
          ...preferences
        }
      })
    }

    return NextResponse.json({ message: '更新成功' })
  } catch (error) {
    console.error('更新用户信息错误:', error)
    return NextResponse.json(
      { error: '更新失败' },
      { status: 500 }
    )
  }
}
