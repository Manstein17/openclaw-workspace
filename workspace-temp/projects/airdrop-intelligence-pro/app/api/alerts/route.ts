import { NextRequest, NextResponse } from 'next/server'

// Mock alerts data
const mockAlerts = [
  {
    id: '1',
    name: 'ZetaChain 空投快照提醒',
    airdropId: '1',
    airdropName: 'ZetaChain',
    alertType: 'snapshot',
    reminderTime: '2026-02-15T10:00:00.000Z',
    isEnabled: true,
    notificationMethod: 'browser',
    createdAt: new Date().toISOString()
  },
  {
    id: '2',
    name: 'LayerZero 任务截止提醒',
    airdropId: '2',
    airdropName: 'LayerZero',
    alertType: 'deadline',
    reminderTime: '2026-02-20T18:00:00.000Z',
    isEnabled: true,
    notificationMethod: 'email',
    createdAt: new Date().toISOString()
  }
]

export async function GET(request: NextRequest) {
  try {
    // In a real app, you would query the database
    // const alerts = await prisma.alert.findMany({
    //   where: { userId: user.id },
    //   orderBy: { createdAt: 'desc' }
    // })
    
    return NextResponse.json({
      success: true,
      data: mockAlerts
    })
  } catch (error) {
    console.error('获取提醒失败:', error)
    return NextResponse.json(
      { success: false, error: '获取提醒失败' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate required fields
    if (!body.airdropId || !body.reminderTime) {
      return NextResponse.json(
        { success: false, error: '缺少必填字段' },
        { status: 400 }
      )
    }
    
    // In a real app, you would create the alert in the database
    // const alert = await prisma.alert.create({
    //   data: {
    //     name: body.name,
    //     airdropId: body.airdropId,
    //     alertType: body.alertType,
    //     reminderTime: new Date(body.reminderTime),
    //     notificationMethod: body.notificationMethod,
    //     userId: user.id
    //   }
    // })
    
    const newAlert = {
      id: Date.now().toString(),
      ...body,
      isEnabled: true,
      createdAt: new Date().toISOString()
    }
    
    return NextResponse.json({
      success: true,
      data: newAlert,
      message: '提醒创建成功'
    })
  } catch (error) {
    console.error('创建提醒失败:', error)
    return NextResponse.json(
      { success: false, error: '创建提醒失败' },
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, ...updateData } = body
    
    // In a real app, you would update the alert in the database
    // const alert = await prisma.alert.update({
    //   where: { id },
    //   data: updateData
    // })
    
    return NextResponse.json({
      success: true,
      message: '提醒更新成功'
    })
  } catch (error) {
    console.error('更新提醒失败:', error)
    return NextResponse.json(
      { success: false, error: '更新提醒失败' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')
    
    if (!id) {
      return NextResponse.json(
        { success: false, error: '缺少提醒ID' },
        { status: 400 }
      )
    }
    
    // In a real app, you would delete the alert from the database
    // await prisma.alert.delete({ where: { id } })
    
    return NextResponse.json({
      success: true,
      message: '提醒删除成功'
    })
  } catch (error) {
    console.error('删除提醒失败:', error)
    return NextResponse.json(
      { success: false, error: '删除提醒失败' },
      { status: 500 }
    )
  }
}
