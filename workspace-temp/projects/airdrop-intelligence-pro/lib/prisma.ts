import { PrismaClient } from '@prisma/client'

// Prisma Client 单例实例
// 在开发环境中避免热重载时创建多个连接
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

export default prisma
