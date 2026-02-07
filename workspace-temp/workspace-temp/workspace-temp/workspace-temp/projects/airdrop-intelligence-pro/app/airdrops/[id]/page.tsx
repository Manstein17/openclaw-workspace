/**
 * Airdrop Detail Page - 空投详情页
 * /app/airdrops/[id]/page.tsx
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { 
  ArrowLeft, ExternalLink, Twitter, MessageCircle, Globe, 
  CheckCircle, Clock, DollarSign, Star, Share2, Bookmark,
  TrendingUp, Award, Target, Zap, ChevronDown, ChevronUp
} from 'lucide-react'
import axios from 'axios'

interface Airdrop {
  id: string
  name: string
  slug: string
  category: string
  status: string
  difficulty: string
  estimatedValue: string
  description: string
  website: string
  twitter: string
  discord: string
  tasks?: Task[]
  createdAt: string
}

interface Task {
  id: string
  title: string
  description: string
  completed: boolean
  difficulty: 'easy' | 'medium' | 'hard'
  points: number
}

export default function AirdropDetailPage() {
  const router = useRouter()
  const params = useParams()
  const airdropId = params?.id as string | undefined
  const [airdrop, setAirdrop] = useState<Airdrop | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'guide'>('overview')
  const [expandedTasks, setExpandedTasks] = useState<string[]>([])

  useEffect(() => {
    if (airdropId) {
      loadAirdrop(airdropId)
    }
  }, [airdropId])

  const loadAirdrop = async (id: string) => {
    try {
      const res = await axios.get(`/api/airdrops?id=${id}`)
      if (res.data.data) {
        setAirdrop(res.data.data[0] || generateMockAirdrop(id))
      } else {
        setAirdrop(generateMockAirdrop(id))
      }
    } catch (error) {
      console.error('加载空投详情失败:', error)
      setAirdrop(generateMockAirdrop(id))
    } finally {
      setLoading(false)
    }
  }

  const generateMockAirdrop = (id: string): Airdrop => {
    const projects: Record<string, any> = {
      '1': {
        name: 'ZetaChain',
        category: 'Layer1',
        description: 'ZetaChain 是第一个也是唯一一个连接加密货币生态系统的 L1 区块链，支持跨链消息传递和原生比特币支持。通过 ZetaChain，用户可以在任何地方构建 dApps，获取加密货币收益等。',
        status: 'active',
        difficulty: 'medium',
        estimatedValue: '$1000-5000',
        website: 'https://zetachain.com',
        twitter: 'https://twitter.com/zetachain',
        discord: 'https://discord.gg/zetachain',
        tasks: [
          { id: '1', title: '连接 ZetaChain 测试网', description: '访问 ZetaChain 官网并连接你的钱包到测试网', completed: false, difficulty: 'easy', points: 10 },
          { id: '2', title: '进行跨链转账', description: '在测试网上进行至少 3 次跨链转账操作', completed: false, difficulty: 'easy', points: 20 },
          { id: '3', title: '添加流动性池', description: '在 ZetaChain 测试网的 DEX 中添加流动性', completed: false, difficulty: 'medium', points: 30 },
          { id: '4', title: 'mint ZRC-20 代币', description: '铸造 ZRC-20 代币并进行跨链转账', completed: false, difficulty: 'medium', points: 30 },
          { id: '5', title: '撰写测试网体验文章', description: '在社交媒体或 Medium 上分享你的 ZetaChain 测试网体验', completed: false, difficulty: 'hard', points: 50 }
        ]
      },
      '2': {
        name: 'LayerZero',
        category: 'Cross-chain',
        description: 'LayerZero 是一个全链互操作性协议，支持跨链消息传递和资产转移。多家知名项目如 Stargate、Radiant 等都建立在 LayerZero 之上，预计将有很大的空投机会。',
        status: 'active',
        difficulty: 'hard',
        estimatedValue: '$500-2000',
        website: 'https://layerzero.network',
        twitter: 'https://twitter.com/LayerZero_Labs',
        discord: 'https://discord.gg/layerzero',
        tasks: [
          { id: '1', title: '使用 Stargate Bridge', description: '使用 Stargate 桥接资产到不同链', completed: false, difficulty: 'easy', points: 15 },
          { id: '2', title: '在 Stargate 中提供流动性', description: '在 Stargate 的流动性池中提供资产', completed: false, difficulty: 'medium', points: 35 },
          { id: '3', title: '进行多链投票', description: '参与 LayerZero 生态项目的链上投票', completed: false, difficulty: 'medium', points: 25 },
          { id: '4', title: 'mint NFT', description: '铸造 LayerZero 相关的 NFT', completed: false, difficulty: 'easy', points: 10 },
          { id: '5', title: '推荐新用户', description: '通过你的推荐链接邀请新用户使用', completed: false, difficulty: 'medium', points: 30 }
        ]
      },
      'default': {
        name: 'Scroll',
        category: 'Layer2',
        description: 'Scroll 是基于 zkEVM 的以太坊 Layer2 解决方案，提供完全兼容以太坊的零知识证明技术。测试网阶段活跃的参与者有望获得空投。',
        status: 'active',
        difficulty: 'medium',
        estimatedValue: '$500-3000',
        website: 'https://scroll.io',
        twitter: 'https://twitter.com/Scroll_ZK',
        discord: 'https://discord.gg/scroll',
        tasks: [
          { id: '1', title: 'Bridge 资产到 Scroll', description: '使用官方桥将 ETH 或其他资产桥接到 Scroll 测试网', completed: false, difficulty: 'easy', points: 10 },
          { id: '2', title: '进行 Swap 交易', description: '在 Scroll 测试网的 DEX 上进行至少 5 次 Swap 交易', completed: false, difficulty: 'easy', points: 15 },
          { id: '3', title: 'mint NFT', description: '铸造 Scroll 生态 NFT', completed: false, difficulty: 'easy', points: 10 },
          { id: '4', title: '使用 NFT 市场', description: '在 Scroll NFT 市场上架或购买 NFT', completed: false, difficulty: 'medium', points: 25 },
          { id: '5', title: '部署智能合约', description: '在 Scroll 测试网上部署自己的智能合约', completed: false, difficulty: 'hard', points: 50 }
        ]
      }
    }
    
    return {
      id: id,
      slug: `${projects[id]?.name?.toLowerCase() || 'unknown'}-${id}`,
      ...projects[id] || projects['default'],
      createdAt: new Date().toISOString()
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'hard': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'pending': return 'bg-yellow-500'
      case 'completed': return 'bg-blue-500'
      case 'ended': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const toggleTask = (taskId: string) => {
    setExpandedTasks(prev => 
      prev.includes(taskId) ? prev.filter(id => id !== taskId) : [...prev, taskId]
    )
  }

  const completedTasksCount = airdrop?.tasks?.filter(t => t.completed).length || 0
  const totalPoints = airdrop?.tasks?.reduce((sum, t) => sum + t.points, 0) || 0
  const earnedPoints = airdrop?.tasks?.filter(t => t.completed).reduce((sum, t) => sum + t.points, 0) || 0

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载空投详情...</p>
        </div>
      </div>
    )
  }

  if (!airdrop) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">未找到该空投项目</p>
          <Link href="/dashboard" className="text-purple-600 hover:underline">
            返回仪表板
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => router.back()}
              className="flex items-center gap-2 text-white/80 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">返回</span>
            </button>
            <div className="h-6 w-px bg-white/20"></div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🏆</span>
              <h1 className="text-xl sm:text-2xl font-bold">{airdrop.name}</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Hero Card */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-6">
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-4 sm:p-8 text-white">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`w-3 h-3 rounded-full ${getStatusColor(airdrop.status)}`}></span>
                  <span className="text-sm opacity-80 capitalize">{airdrop.status === 'active' ? '进行中' : airdrop.status}</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-bold mb-2">{airdrop.name}</h1>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="px-3 py-1 bg-white/20 rounded-full">{airdrop.category}</span>
                  <span className={`px-3 py-1 rounded-full ${getDifficultyColor(airdrop.difficulty)}`}>
                    难度: {airdrop.difficulty === 'easy' ? '简单' : airdrop.difficulty === 'medium' ? '中等' : '困难'}
                  </span>
                  <span className="px-3 py-1 bg-yellow-400/20 text-yellow-300 rounded-full flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    {airdrop.estimatedValue}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors" title="收藏">
                  <Bookmark className="w-5 h-5" />
                </button>
                <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors" title="分享">
                  <Share2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-4 p-4 sm:p-6 bg-gray-50">
            <div className="text-center">
              <div className="text-2xl sm:text-3xl font-bold text-purple-600">{completedTasksCount}/{airdrop.tasks?.length || 0}</div>
              <div className="text-sm text-gray-500">完成任务</div>
            </div>
            <div className="text-center">
              <div className="text-2xl sm:text-3xl font-bold text-green-600">{earnedPoints}/{totalPoints}</div>
              <div className="text-sm text-gray-500">获得积分</div>
            </div>
            <div className="text-center">
              <div className="text-2xl sm:text-3xl font-bold text-blue-600">
                {totalPoints > 0 ? Math.round((earnedPoints / totalPoints) * 100) : 0}%
              </div>
              <div className="text-sm text-gray-500">完成进度</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="px-4 sm:px-6 pb-4 sm:pb-6">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-purple-500 to-indigo-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${totalPoints > 0 ? (earnedPoints / totalPoints) * 100 : 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Social Links */}
        <div className="flex flex-wrap gap-2 mb-6">
          <a 
            href={airdrop.website} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Globe className="w-4 h-4" />
            官网
          </a>
          <a 
            href={airdrop.twitter} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Twitter className="w-4 h-4" />
            Twitter
          </a>
          <a 
            href={airdrop.discord} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <MessageCircle className="w-4 h-4" />
            Discord
          </a>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="flex border-b">
            {[
              { id: 'overview', label: '项目概览', icon: Target },
              { id: 'tasks', label: '任务列表', icon: CheckCircle },
              { id: 'guide', label: '操作教程', icon: Zap }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex-1 flex items-center justify-center gap-2 py-4 px-4 text-sm font-medium transition-colors ${
                  activeTab === tab.id 
                    ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50' 
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-4 sm:p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Award className="w-5 h-5 text-purple-600" />
                    项目介绍
                  </h3>
                  <p className="text-gray-600 leading-relaxed">{airdrop.description}</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Star className="w-4 h-4 text-yellow-500" />
                      项目亮点
                    </h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• 热门空投项目，持续活跃</li>
                      <li>• 社区规模大，关注度高</li>
                      <li>• 已完成多轮融资</li>
                    </ul>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      空投预期
                    </h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• 预估价值: {airdrop.estimatedValue}</li>
                      <li>• 难度等级: {airdrop.difficulty}</li>
                      <li>• 建议积极参与测试网</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Tasks Tab */}
            {activeTab === 'tasks' && (
              <div className="space-y-3">
                {airdrop.tasks?.map((task, index) => (
                  <div 
                    key={task.id}
                    className={`border rounded-lg overflow-hidden transition-colors ${
                      task.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <button
                      onClick={() => toggleTask(task.id)}
                      className="w-full p-4 flex items-center justify-between text-left"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          task.completed ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'
                        }`}>
                          {task.completed ? <CheckCircle className="w-5 h-5" /> : <span className="font-medium">{index + 1}</span>}
                        </div>
                        <div>
                          <h4 className={`font-medium ${task.completed ? 'line-through text-gray-500' : ''}`}>
                            {task.title}
                          </h4>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getDifficultyColor(task.difficulty)}`}>
                              {task.difficulty === 'easy' ? '简单' : task.difficulty === 'medium' ? '中等' : '困难'}
                            </span>
                            <span className="text-xs text-gray-500">+{task.points} 积分</span>
                          </div>
                        </div>
                      </div>
                      {expandedTasks.includes(task.id) ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </button>
                    
                    {expandedTasks.includes(task.id) && (
                      <div className="px-4 pb-4 pl-16">
                        <p className="text-sm text-gray-600 mb-3">{task.description}</p>
                        <button
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                            task.completed 
                              ? 'bg-gray-200 text-gray-600 cursor-default'
                              : 'bg-green-500 text-white hover:bg-green-600'
                          }`}
                        >
                          {task.completed ? '已完成' : '标记为完成'}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Guide Tab */}
            {activeTab === 'guide' && (
              <div className="space-y-6">
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-medium text-blue-700 mb-2 flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    开始之前
                  </h3>
                  <p className="text-sm text-blue-600">
                    确保你已安装 MetaMask 或其他钱包，并准备一些测试网 ETH 用于支付 Gas 费用。
                  </p>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Zap className="w-5 h-5 text-purple-600" />
                    快速开始指南
                  </h3>
                  
                  <div className="space-y-3">
                    {[
                      { step: 1, title: '访问官网', desc: '点击右上角"官网"按钮访问项目官网' },
                      { step: 2, title: '连接钱包', desc: '点击"Connect Wallet"并选择你的钱包' },
                      { step: 3, title: '切换到测试网', desc: '在钱包中切换到对应的测试网' },
                      { step: 4, title: '开始交互', desc: '按照任务列表开始进行各种交互操作' },
                      { step: 5, title: '持续参与', desc: '保持活跃，定期回来检查新任务' }
                    ].map(item => (
                      <div key={item.step} className="flex gap-4">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="font-medium text-purple-600">{item.step}</span>
                        </div>
                        <div>
                          <h4 className="font-medium">{item.title}</h4>
                          <p className="text-sm text-gray-600">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-700 mb-2">⚠️ 注意事项</h3>
                  <ul className="text-sm text-yellow-600 space-y-1">
                    <li>• 只使用测试网进行交互，不要使用真钱</li>
                    <li>• 保留所有交互记录和截图作为凭证</li>
                    <li>• 避免使用多个账户，可能会被视为作弊</li>
                    <li>• 关注官方渠道获取最新消息</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
