'use client'

import Link from 'next/link'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'

export default function PricingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-black">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="container mx-auto px-4 py-3 sm:py-4 flex justify-between items-center">
          <Link href="/" className="text-lg sm:text-2xl font-bold flex items-center gap-2">
            <span className="text-2xl">🏆</span>
            <span className="hidden sm:inline">空投情报局 Pro</span>
            <span className="sm:hidden">空投Pro</span>
          </Link>
          
          {/* Desktop menu */}
          <div className="hidden sm:flex gap-4">
            <Link href="/dashboard" className="btn-primary text-sm">
              免费试用
            </Link>
          </div>

          {/* Mobile menu button */}
          <button 
            className="sm:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-white/10 py-4 px-4">
            <Link 
              href="/dashboard" 
              className="block py-3 text-center bg-purple-600 rounded-lg mb-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              免费试用
            </Link>
            <Link 
              href="/login" 
              className="block py-3 text-center border border-white/20 rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              登录
            </Link>
          </div>
        )}
      </nav>

      {/* Hero */}
      <section className="pt-20 sm:pt-24 pb-12 sm:pb-16 px-4">
        <div className="container mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
            💰 <span className="gradient-text">灵活定价</span>
          </h1>
          <p className="text-gray-400 mb-8 text-sm sm:text-base px-4">
            根据你的需求选择合适的方案
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-16 sm:pb-20 px-4">
        <div className="container mx-auto">
          {/* Mobile: 1 column, Tablet: 2 columns, Desktop: 4 columns */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 max-w-6xl mx-auto">
            {/* Free */}
            <div className="glass-card p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-400 text-center">体验卡</h3>
              <div className="text-2xl sm:text-4xl font-bold my-3 sm:my-4 text-center text-white">¥9.9</div>
              <p className="text-xs sm:text-sm text-gray-500 text-center mb-3 sm:mb-4">7天有效</p>
              <ul className="text-xs sm:text-sm space-y-2 text-gray-300 mb-4 sm:mb-6">
                <li>✅ 基础空投发现</li>
                <li>✅ 每日简报</li>
                <li>❌ 无实时推送</li>
                <li>❌ 无操作指南</li>
              </ul>
              <Link href="/register" className="btn-secondary w-full text-center block py-2 sm:py-3 text-sm sm:text-base">
                了解更多
              </Link>
            </div>

            {/* Monthly */}
            <div className="glass-card p-4 sm:p-6 border-purple-500 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-purple-500 text-white px-3 py-1 rounded-full text-xs">
                最推荐
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-purple-400 text-center">月卡</h3>
              <div className="text-2xl sm:text-4xl font-bold my-3 sm:my-4 text-center text-purple-400">¥29</div>
              <p className="text-xs sm:text-sm text-gray-500 text-center mb-3 sm:mb-4">30天有效</p>
              <ul className="text-xs sm:text-sm space-y-2 text-gray-300 mb-4 sm:mb-6">
                <li>✅ 全部空投发现</li>
                <li>✅ 实时推送</li>
                <li>✅ 操作指南</li>
                <li>✅ 社群支持</li>
              </ul>
              <Link href="/register" className="btn-primary w-full text-center block py-2 sm:py-3 text-sm sm:text-base">
                立即购买
              </Link>
            </div>

            {/* Quarterly */}
            <div className="glass-card p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-400 text-center">季卡</h3>
              <div className="text-2xl sm:text-4xl font-bold my-3 sm:my-4 text-center text-white">¥79</div>
              <p className="text-xs sm:text-sm text-gray-500 text-center mb-3 sm:mb-4">90天有效</p>
              <ul className="text-xs sm:text-sm space-y-2 text-gray-300 mb-4 sm:mb-6">
                <li>✅ 全部功能</li>
                <li>✅ 优先支持</li>
                <li>✅ 专属社群</li>
                <li>✅ 额外福利</li>
              </ul>
              <Link href="/register" className="btn-secondary w-full text-center block py-2 sm:py-3 text-sm sm:text-base">
                节省 9%
              </Link>
            </div>

            {/* Yearly */}
            <div className="glass-card p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-400 text-center">年卡</h3>
              <div className="text-2xl sm:text-4xl font-bold my-3 sm:my-4 text-center text-white">¥199</div>
              <p className="text-xs sm:text-sm text-gray-500 text-center mb-3 sm:mb-4">365天有效</p>
              <ul className="text-xs sm:text-sm space-y-2 text-gray-300 mb-4 sm:mb-6">
                <li>✅ 全部功能</li>
                <li>✅ 最高优先级</li>
                <li>✅ 专属客服</li>
                <li>✅ 未来产品免费</li>
              </ul>
              <Link href="/register" className="btn-secondary w-full text-center block py-2 sm:py-3 text-sm sm:text-base">
                节省 43%
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-6 sm:py-8 text-center text-gray-500 text-xs sm:text-sm px-4">
        <p>© 2026 空投情报局 Pro. All rights reserved.</p>
      </footer>
    </div>
  )
}
