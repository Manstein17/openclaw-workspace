import { NextResponse } from 'next/server'
import prisma from '@/lib/prisma'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { email, activationCode } = body

    // 参数验证
    if (!email || !activationCode) {
      return NextResponse.json(
        { error: '请提供邮箱和激活码' },
        { status: 400 }
      )
    }

    // 查找激活码
    const code = await prisma.activationCode.findUnique({
      where: { code: activationCode.toUpperCase() }
    })

    if (!code) {
      return NextResponse.json(
        { error: '激活码无效' },
        { status: 400 }
      )
    }

    // 检查激活码是否激活
    if (!code.isActive) {
      return NextResponse.json(
        { error: '激活码已被使用或已禁用' },
        { status: 400 }
      )
    }

    // 检查激活码是否过期
    if (code.expiresAt && new Date(code.expiresAt) < new Date()) {
      return NextResponse.json(
        { error: '激活码已过期' },
        { status: 400 }
      )
    }

    // 检查激活码使用次数
    if (code.usedCount >= code.maxUsers) {
      return NextResponse.json(
        { error: '激活码已达到最大使用次数' },
        { status: 400 }
      )
    }

    // 查找用户
    const user = await prisma.user.findUnique({
      where: { email }
    })

    if (!user) {
      return NextResponse.json(
        { error: '用户不存在，请先注册' },
        { status: 400 }
      )
    }

    // 计算过期日期
    const startDate = new Date()
    const expireDate = new Date(startDate)
    expireDate.setDate(expireDate.getDate() + code.durationDays)

    // 更新用户订阅
    await prisma.subscription.upsert({
      where: { userId: user.id },
      update: {
        plan: code.plan,
        status: 'active',
        startDate,
        expireDate,
        activationCodeId: code.id,
      },
      create: {
        userId: user.id,
        plan: code.plan,
        status: 'active',
        startDate,
        expireDate,
        activationCodeId: code.id,
      }
    })

    // 更新激活码使用次数
    await prisma.activationCode.update({
      where: { id: code.id },
      data: {
        usedCount: {
          increment: 1
        }
      }
    })

    return NextResponse.json({
      message: '激活成功！您现在可以享受 Pro 会员权益',
      plan: code.plan,
      expireDate
    })
  } catch (error) {
    console.error('激活错误:', error)
    return NextResponse.json(
      { error: '激活失败，请稍后重试' },
      { status: 500 }
    )
  }
}
