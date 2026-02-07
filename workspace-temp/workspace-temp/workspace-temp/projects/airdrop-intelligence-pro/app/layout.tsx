import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Providers from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '空投情报局 Pro - 专业空投资讯监控服务',
  description: '帮你找到 + 筛选 + 指导操作空投机会',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className="dark">
      <body className={`${inter.className} gradient-bg tech-grid-bg min-h-screen antialiased`}>
        {/* 科技感装饰元素 */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          {/* 动态光球 */}
          <div className="floating-orb w-[500px] h-[500px] bg-purple-600/20 top-[-200px] left-[-200px]" />
          <div className="floating-orb w-[400px] h-[400px] bg-blue-600/15 bottom-[-150px] right-[-150px]" style={{ animationDelay: '2s' }} />
          <div className="floating-orb w-[300px] h-[300px] bg-cyan-500/10 top-[40%] right-[10%]" style={{ animationDelay: '4s' }} />
          
          {/* 扫描线效果 */}
          <div className="scanline" />
        </div>
        
        {/* 主内容 */}
        <div className="relative z-10 pb-16 sm:pb-0">
          <Providers>
            {children}
          </Providers>
        </div>
      </body>
    </html>
  )
}
