/**
 * 添加监控项目页面
 * /app/airdrops/add/page.tsx
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Search, Plus, Star, ExternalLink } from 'lucide-react'
import axios from 'axios'

interface AirdropProject {
  id: string
  name: string
  category: string
  status: string
  description: string
  website: string
  discord: string
  twitter: string
}

const popularProjects = [
  { name: 'ZetaChain', category: 'Layer1', website: 'https://zetachain.com' },
  { name: 'LayerZero', category: 'Cross-chain', website: 'https://layerzero.network' },
  { name: 'Scroll', category: 'Layer2', website: 'https://scroll.io' },
  { name: 'Linea', category: 'Layer2', website: 'https://linea.build' },
  { name: 'Starknet', category: 'Layer2', website: 'https://starknet.io' },
  { name: 'Arbitrum', category: 'Layer2', website: 'https://arbitrum.io' },
  { name: 'Optimism', category: 'Layer2', website: 'https://optimism.io' },
  { name: 'Base', category: 'Layer2', website: 'https://base.org' },
  { name: 'zkSync', category: 'Layer2', website: 'https://zksync.io' },
  { name: 'Blast', category: 'Layer2', website: 'https://blast.io' },
  { name: 'EigenLayer', category: 'Restaking', website: 'https://eigenlayer.xyz' },
  { name: 'Mantle', category: 'Layer2', website: 'https://mantle.xyz' },
  { name: 'Taiko', category: 'Layer2', website: 'https://taiko.xyz' },
  { name: 'Metis', category: 'Layer2', website: 'https://metis.io' },
  { name: 'Aleo', category: 'Privacy', website: 'https://aleo.org' },
  { name: 'Sui', category: 'Layer1', website: 'https://sui.io' },
  { name: 'Aptos', category: 'Layer1', website: 'https://aptoslabs.com' },
  { name: 'Sei', category: 'Layer1', website: 'https://sei.io' }
]

export default function AddAirdropPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState('')
  const [customName, setCustomName] = useState('')
  const [customWebsite, setCustomWebsite] = useState('')
  const [customCategory, setCustomCategory] = useState('Layer2')
  const [monitoredProjects, setMonitoredProjects] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // 加载已监控的项目
  useEffect(() => {
    async function loadMonitored() {
      try {
        const res = await axios.get('/api/airdrops')
        if (res.data.data) {
          setMonitoredProjects(res.data.data.map((p: AirdropProject) => p.name))
        }
      } catch (error) {
        console.error('加载已监控项目失败:', error)
      }
    }
    loadMonitored()
  }, [])

  // 过滤搜索结果
  const filteredProjects = popularProjects.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !monitoredProjects.includes(p.name)
  )

  // 添加项目到监控列表
  const addProject = async (project: typeof popularProjects[0]) => {
    setLoading(true)
    setMessage(null)

    try {
      await axios.post('/api/airdrops', {
        name: project.name,
        category: project.category,
        website: project.website,
        status: 'pending',
        difficulty: 'medium',
        description: `热门空投项目 - ${project.category}`
      })

      setMessage({ type: 'success', text: `✅ ${project.name} 已添加到监控列表` })
      setMonitoredProjects([...monitoredProjects, project.name])
      
      // 3秒后清除消息
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.error || '添加失败' })
    } finally {
      setLoading(false)
    }
  }

  // 添加自定义项目
  const addCustomProject = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!customName || !customWebsite) {
      setMessage({ type: 'error', text: '请填写项目名称和官网' })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      await axios.post('/api/airdrops', {
        name: customName,
        category: customCategory,
        website: customWebsite,
        status: 'pending',
        difficulty: 'medium',
        description: '用户自定义添加的空投项目'
      })

      setMessage({ type: 'success', text: `✅ ${customName} 已添加` })
      setCustomName('')
      setCustomWebsite('')
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.error || '添加失败' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/dashboard" className="text-2xl font-bold flex items-center gap-2">
            <span className="text-3xl">🏆</span>
            <span>空投情报局 Pro</span>
          </Link>
          
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="hover:text-purple-200 transition-colors">
              返回仪表板
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">添加监控项目</h1>

        {/* 消息显示 */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 搜索添加热门项目 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-purple-600" />
              搜索并添加热门项目
            </h2>

            {/* 搜索框 */}
            <div className="mb-4">
              <input
                type="text"
                placeholder="搜索项目名称..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* 项目列表 */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredProjects.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {monitoredProjects.length >= popularProjects.length 
                    ? '已添加所有热门项目' 
                    : '没有找到匹配的项目'}
                </p>
              ) : (
                filteredProjects.map((project) => (
                  <div key={project.name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        {project.name}
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                          {project.category}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                        <ExternalLink className="w-3 h-3" />
                        {project.website}
                      </div>
                    </div>
                    <button
                      onClick={() => addProject(project)}
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                    >
                      <Plus className="w-4 h-4" />
                      添加
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* 统计信息 */}
            <div className="mt-4 pt-4 border-t text-sm text-gray-500">
              已监控 {monitoredProjects.length} / {popularProjects.length} 个热门项目
            </div>
          </div>

          {/* 添加自定义项目 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5 text-purple-600" />
              添加自定义项目
            </h2>

            <form onSubmit={addCustomProject} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目名称 *
                </label>
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  placeholder="输入项目名称"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目分类
                </label>
                <select
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="Layer1">Layer1</option>
                  <option value="Layer2">Layer2</option>
                  <option value="Cross-chain">Cross-chain</option>
                  <option value="DEX">DEX</option>
                  <option value="DeFi">DeFi</option>
                  <option value="NFT">NFT</option>
                  <option value="Gaming">Gaming</option>
                  <option value="Privacy">Privacy</option>
                  <option value="Restaking">Restaking</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  官网链接 *
                </label>
                <input
                  type="url"
                  value={customWebsite}
                  onChange={(e) => setCustomWebsite(e.target.value)}
                  placeholder="https://"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    添加中...
                  </>
                ) : (
                  <>
                    <Plus className="w-5 h-5" />
                    添加项目
                  </>
                )}
              </button>
            </form>

            {/* 提示信息 */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-700 mb-2">💡 提示</h3>
              <ul className="text-sm text-blue-600 space-y-1">
                <li>• 添加项目后，系统会自动监控该项目的空投资讯</li>
                <li>• 热门项目会自动同步最新的空投动态</li>
                <li>• 自定义项目需要手动关注最新消息</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 已监控项目列表 */}
        {monitoredProjects.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              已监控的项目
            </h2>
            <div className="flex flex-wrap gap-2">
              {monitoredProjects.map((name) => (
                <span
                  key={name}
                  className="px-4 py-2 bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-700 rounded-full font-medium"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
