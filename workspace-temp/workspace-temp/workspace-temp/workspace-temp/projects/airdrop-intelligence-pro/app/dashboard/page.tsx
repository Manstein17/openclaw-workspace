'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useSession, signOut } from 'next-auth/react'
import axios from 'axios'
import { Menu, X, ChevronRight } from 'lucide-react'

// 模拟的空投数据
const mockAirdrops = [
  {
    id: 1,
    name: 'Zeko Network',
    category: 'Layer2',
    status: 'Active',
    score: 85,
    risk: 'Low',
    description: '基于零知识证明的Layer2网络，支持隐私交易',
    lastUpdated: '2小时前'
  },
  {
    id: 2,
    name: 'Lighter',
    category: 'DEX',
    status: 'Active',
    score: 78,
    risk: 'Medium',
    description: '零Gas费DEX，多阶段积分系统',
    lastUpdated: '4小时前'
  },
  {
    id: 3,
    name: 'LayerZero',
    category: 'Cross-chain',
    status: 'Pending',
    score: 92,
    risk: 'Medium',
    description: '跨链消息协议，社区期待的空投项目',
    lastUpdated: '1天前'
  },
  {
    id: 4,
    name: 'EigenLayer',
    category: 'Restaking',
    status: 'Active',
    score: 75,
    risk: 'Low',
    description: 'ETH再质押协议，已发币，持续激励',
    lastUpdated: '6小时前'
  }
]

interface UserData {
  name: string
  email: string
  subscription?: {
    plan: string
    status: string
    expireDate?: string
  }
}

interface Airdrop {
  id: string
  name: string
  category: string
  status: string
  difficulty: string
  description?: string
  startDate?: string
  estimatedValue?: string
  twitter?: string
  discord?: string
  website?: string
}

export default function Dashboard() {
  const { data: session, status } = useSession()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [airdrops, setAirdrops] = useState<Airdrop[]>([])
  const [loading, setLoading] = useState(true)
  const [activationCode, setActivationCode] = useState('')
  const [activating, setActivating] = useState(false)
  const [activationMessage, setActivationMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // 加载用户数据和空投列表
  useEffect(() => {
    async function loadData() {
      try {
        // 获取用户信息
        if (session?.user) {
          const userRes = await axios.get('/api/user')
          setUserData(userRes.data.user)
        } else if (status === 'unauthenticated') {
          // 未登录时使用默认数据
          setUserData({
            name: '访客',
            email: 'guest@example.com',
            subscription: {
              plan: 'free',
              status: 'active'
            }
          })
          setAirdrops(mockAirdrops as any)
          setLoading(false)
          return
        } else {
          // 等待 session 加载
          return
        }

        // 获取空投列表
        const airdropsRes = await axios.get('/api/airdrops')
        if (airdropsRes.data.data && airdropsRes.data.data.length > 0) {
          setAirdrops(airdropsRes.data.data)
        } else {
          // 如果数据库为空，使用模拟数据
          setAirdrops(mockAirdrops as any)
        }
      } catch (error) {
        console.error('加载数据错误:', error)
        // 使用模拟数据作为后备
        setAirdrops(mockAirdrops as any)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [session, status])

  // 处理激活码
  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault()
    setActivating(true)
    setActivationMessage(null)

    try {
      await axios.post('/api/activate', {
        email: userData?.email || '',
        activationCode
      })
      setActivationMessage({ type: 'success', text: '激活成功！请刷新页面查看' })
      setActivationCode('')
    } catch (error: any) {
      setActivationMessage({ 
        type: 'error', 
        text: error.response?.data?.error || '激活失败，请检查激活码' 
      })
    } finally {
      setActivating(false)
    }
  }

  // 获取订阅状态显示
  const getSubscriptionDisplay = () => {
    const plan = userData?.subscription?.plan || 'free'
    const planNames: Record<string, string> = {
      free: '免费版',
      basic: '基础版',
      pro: 'Pro版',
      enterprise: '企业版'
    }
    
    return planNames[plan] || plan
  }

  // 渲染状态标签
  const renderStatus = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      upcoming: { label: '即将开始', className: 'bg-blue-100 text-blue-700' },
      active: { label: '进行中', className: 'bg-green-100 text-green-700' },
      ended: { label: '已结束', className: 'bg-gray-100 text-gray-700' }
    }
    
    const config = statusMap[status] || { label: status, className: 'bg-gray-100 text-gray-700' }
    return (
      <span className={`px-2 py-1 rounded text-xs ${config.className}`}>
        {config.label}
      </span>
    )
  }

  // 渲染难度标签
  const renderDifficulty = (difficulty: string) => {
    const difficultyMap: Record<string, { label: string; className: string }> = {
      easy: { label: '简单', className: 'bg-green-100 text-green-700' },
      medium: { label: '中等', className: 'bg-yellow-100 text-yellow-700' },
      hard: { label: '困难', className: 'bg-red-100 text-red-700' }
    }
    
    const config = difficultyMap[difficulty] || { label: difficulty, className: 'bg-gray-100 text-gray-700' }
    return (
      <span className={`px-2 py-1 rounded text-xs ${config.className}`}>
        {config.label}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link href="/" className="text-xl sm:text-2xl font-bold flex items-center gap-2">
              <span className="text-2xl">🏆</span>
              <span className="hidden sm:inline">空投情报局 Pro</span>
              <span className="sm:hidden">空投Pro</span>
            </Link>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <nav className="flex items-center gap-6">
                <Link href="/dashboard" className="text-white hover:text-purple-200 transition-colors">
                  仪表板
                </Link>
                <Link href="/airdrops/add" className="text-white hover:text-purple-200 transition-colors">
                  添加项目
                </Link>
                <Link href="/reports" className="text-white hover:text-purple-200 transition-colors">
                  报告
                </Link>
                <Link href="/alerts" className="text-white hover:text-purple-200 transition-colors">
                  提醒
                </Link>
              </nav>

              {/* User Info */}
              <div className="flex items-center gap-4">
                <div className="text-right hidden lg:block">
                  <div className="font-medium">{userData?.name || '访客'}</div>
                  <div className="text-xs text-purple-200">
                    {getSubscriptionDisplay()}
                  </div>
                </div>
                
                {session ? (
                  <button
                    onClick={() => signOut({ callbackUrl: '/login' })}
                    className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors"
                  >
                    退出
                  </button>
                ) : (
                  <Link
                    href="/login"
                    className="bg-white text-purple-900 px-4 py-2 rounded-lg font-medium hover:bg-white/90 transition-colors"
                  >
                    登录
                  </Link>
                )}
              </div>
            </div>

            {/* Mobile Menu Button */}
            <button 
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden mt-4 pb-4 border-t border-white/20 pt-4">
              <nav className="flex flex-col gap-2">
                <Link 
                  href="/dashboard" 
                  className="py-3 px-4 hover:bg-white/10 rounded-lg transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  仪表板
                </Link>
                <Link 
                  href="/airdrops/add" 
                  className="py-3 px-4 hover:bg-white/10 rounded-lg transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  添加项目
                </Link>
                <Link 
                  href="/reports" 
                  className="py-3 px-4 hover:bg-white/10 rounded-lg transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  报告
                </Link>
                <Link 
                  href="/alerts" 
                  className="py-3 px-4 hover:bg-white/10 rounded-lg transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  提醒
                </Link>
                <div className="border-t border-white/20 pt-2 mt-2">
                  <div className="px-4 py-2 text-sm text-purple-200">
                    {userData?.name || '访客'} - {getSubscriptionDisplay()}
                  </div>
                  {session ? (
                    <button
                      onClick={() => signOut({ callbackUrl: '/login' })}
                      className="w-full text-left py-3 px-4 hover:bg-white/10 rounded-lg transition-colors"
                    >
                      退出登录
                    </button>
                  ) : (
                    <Link 
                      href="/login" 
                      className="block py-3 px-4 hover:bg-white/10 rounded-lg transition-colors"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      登录
                    </Link>
                  )}
                </div>
              </nav>
            </div>
          )}
        </div>
      </header>

      {/* Stats Cards */}
      <section className="container mx-auto px-4 py-6 sm:py-8">
        {/* Mobile: 2x2 grid, Desktop: 4 columns */}
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          <div className="bg-white p-4 sm:p-6 rounded-xl shadow hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <span className="text-xl sm:text-2xl">📊</span>
              </div>
              <span className="text-green-500 text-xs font-medium hidden sm:inline">+2</span>
            </div>
            <div className="text-xl sm:text-3xl font-bold text-gray-800">{airdrops.length}</div>
            <div className="text-xs sm:text-gray-500 text-gray-400">监控项目</div>
          </div>
          
          <div className="bg-white p-4 sm:p-6 rounded-xl shadow hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <span className="text-xl sm:text-2xl">✅</span>
              </div>
              <span className="text-green-500 text-xs font-medium hidden sm:inline">进行中</span>
            </div>
            <div className="text-xl sm:text-3xl font-bold text-gray-800">
              {airdrops.filter(a => a.status === 'active').length}
            </div>
            <div className="text-xs sm:text-gray-500 text-gray-400">可参与</div>
          </div>
          
          <div className="bg-white p-4 sm:p-6 rounded-xl shadow hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                <span className="text-xl sm:text-2xl">⏰</span>
              </div>
              <span className="text-orange-500 text-xs font-medium hidden sm:inline">即将</span>
            </div>
            <div className="text-xl sm:text-3xl font-bold text-gray-800">
              {airdrops.filter(a => a.status === 'upcoming').length}
            </div>
            <div className="text-xs sm:text-gray-500 text-gray-400">即将开始</div>
          </div>
          
          <div className="bg-white p-4 sm:p-6 rounded-xl shadow hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <span className="text-xl sm:text-2xl">💎</span>
              </div>
            </div>
            <div className="text-xl sm:text-3xl font-bold text-gray-800 hidden sm:block">{getSubscriptionDisplay()}</div>
            <div className="text-lg sm:text-3xl font-bold text-gray-800 sm:hidden">{getSubscriptionDisplay().split('版')[0]}</div>
            <div className="text-xs sm:text-gray-500 text-gray-400">当前套餐</div>
          </div>
        </div>

        {/* Main Content - Stack on mobile */}
        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          {/* Airdrop List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow">
              <div className="p-4 sm:p-6 border-b flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <h2 className="text-lg sm:text-xl font-semibold flex items-center gap-2">
                  🚀 空投监控列表
                </h2>
                <button 
                  onClick={() => window.location.reload()}
                  className="text-blue-600 hover:underline flex items-center gap-1 text-sm"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  刷新
                </button>
              </div>
              
              <div className="divide-y">
                {airdrops.map((airdrop) => (
                  <div key={airdrop.id} className="p-4 sm:p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-base sm:text-lg text-gray-800 truncate">
                          {airdrop.name}
                        </h3>
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                          <span className="text-xs sm:text-sm text-gray-500">{airdrop.category}</span>
                          {airdrop.estimatedValue && (
                            <span className="text-xs sm:text-sm text-green-600 font-medium">
                              预估: {airdrop.estimatedValue}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-1 sm:gap-2 ml-2">
                        {renderStatus(airdrop.status)}
                        {renderDifficulty(airdrop.difficulty)}
                      </div>
                    </div>
                    
                    <p className="text-gray-600 mb-3 line-clamp-2 text-sm">
                      {airdrop.description || '暂无描述'}
                    </p>
                    
                    {/* Links */}
                    <div className="flex flex-wrap gap-2 sm:gap-3 mb-3">
                      {airdrop.website && (
                        <a 
                          href={airdrop.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-xs sm:text-sm flex items-center gap-1"
                        >
                          官网
                        </a>
                      )}
                      {airdrop.twitter && (
                        <a 
                          href={airdrop.twitter} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:underline text-xs sm:text-sm flex items-center gap-1"
                        >
                          Twitter
                        </a>
                      )}
                      {airdrop.discord && (
                        <a 
                          href={airdrop.discord} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-indigo-500 hover:underline text-xs sm:text-sm flex items-center gap-1"
                        >
                          Discord
                        </a>
                      )}
                    </div>
                    
                    <div className="flex justify-between items-center">
                      {airdrop.startDate && (
                        <span className="text-xs text-gray-500 hidden sm:block">
                          开始: {new Date(airdrop.startDate).toLocaleDateString()}
                        </span>
                      )}
                      <button className="text-blue-600 hover:underline text-sm flex items-center gap-1 ml-auto">
                        查看详情
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4 sm:space-y-6">
            {/* 激活码输入 */}
            {userData?.subscription?.plan === 'free' && (
              <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 sm:p-6 rounded-xl shadow-lg">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <span>🎁</span> 激活 Pro 会员
                </h3>
                <p className="text-xs sm:text-sm opacity-90 mb-4">
                  输入激活码，解锁全部高级功能
                </p>
                
                <form onSubmit={handleActivate} className="space-y-3">
                  <input
                    type="text"
                    value={activationCode}
                    onChange={(e) => setActivationCode(e.target.value.toUpperCase())}
                    placeholder="XXXX-XXXX-XXXX"
                    className="w-full px-4 py-2 rounded-lg text-gray-800 placeholder-gray-400 font-mono tracking-wider uppercase text-sm"
                  />
                  
                  {activationMessage && (
                    <div className={`text-xs sm:text-sm p-2 rounded ${
                      activationMessage.type === 'success' 
                        ? 'bg-green-500/20 border border-green-500/50' 
                        : 'bg-red-500/20 border border-red-500/50'
                    }`}>
                      {activationMessage.text}
                    </div>
                  )}
                  
                  <button
                    type="submit"
                    disabled={activating || !activationCode}
                    className="w-full bg-white text-purple-600 py-2 rounded-lg font-semibold hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {activating ? '激活中...' : '立即激活'}
                  </button>
                </form>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white p-4 sm:p-6 rounded-xl shadow">
              <h3 className="font-semibold mb-3 sm:mb-4 flex items-center gap-2">
                <span>⚡</span> 快速操作
              </h3>
              <div className="space-y-2 sm:space-y-3">
                <Link 
                  href="/airdrops/add"
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-2.5 sm:py-2 rounded-lg hover:shadow-lg transition-shadow flex items-center justify-center gap-2 block text-sm sm:text-base"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  添加监控项目
                </Link>
                <Link 
                  href="/reports"
                  className="w-full border border-gray-300 py-2.5 sm:py-2 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2 block text-sm sm:text-base"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  生成报告
                </Link>
                <Link 
                  href="/alerts"
                  className="w-full border border-gray-300 py-2.5 sm:py-2 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2 block text-sm sm:text-base"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  设置提醒
                </Link>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white p-4 sm:p-6 rounded-xl shadow">
              <h3 className="font-semibold mb-3 sm:mb-4 flex items-center gap-2">
                <span>📈</span> 近期动态
              </h3>
              <div className="space-y-3 text-xs sm:text-sm">
                <div className="flex gap-3">
                  <span className="text-blue-600">🔔</span>
                  <div>
                    <p className="text-gray-600">Zeko Network 更新任务</p>
                    <p className="text-gray-400 text-xs">2小时前</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <span className="text-green-600">✅</span>
                  <div>
                    <p className="text-gray-600">Lighter 新积分系统</p>
                    <p className="text-gray-400 text-xs">4小时前</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <span className="text-orange-600">⚠️</span>
                  <div>
                    <p className="text-gray-600">LayerZero 讨论热烈</p>
                    <p className="text-gray-400 text-xs">1天前</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Subscription */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 sm:p-6 rounded-xl shadow-lg">
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <span>💎</span> 升级套餐
              </h3>
              <p className="text-xs sm:text-sm opacity-90 mb-4">
                升级年卡，解锁全部功能
              </p>
              <button className="w-full bg-white text-blue-600 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                了解详情
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
