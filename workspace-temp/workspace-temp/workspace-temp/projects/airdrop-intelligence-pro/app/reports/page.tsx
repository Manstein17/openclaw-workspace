/**
 * 报告生成页面
 * /app/reports/page.tsx
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { FileText, Download, Calendar, TrendingUp, TrendingDown, Award, Clock, BarChart3, PieChart, Filter, RefreshCw } from 'lucide-react'
import axios from 'axios'
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns'

interface Airdrop {
  id: string
  name: string
  category: string
  status: string
  estimatedValue: string | null
  createdAt: string
  completedTasks?: number
  totalTasks?: number
}

interface ReportData {
  totalAirdrops: number
  activeAirdrops: number
  pendingAirdrops: number
  completedAirdrops: number
  totalEstimatedValue: string
  categoryDistribution: Record<string, number>
  monthlyTrend: { month: string; count: number }[]
  recentActivity: { date: string; action: string; airdrop: string }[]
}

export default function ReportsPage() {
  const router = useRouter()
  const [reportData, setReportData] = useState<ReportData | null>(null)
  const [airdrops, setAirdrops] = useState<Airdrop[]>([])
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState<'week' | 'month' | 'all'>('month')
  const [exporting, setExporting] = useState(false)

  // 加载数据
  useEffect(() => {
    async function loadData() {
      try {
        // 获取空投列表
        const airdropsRes = await axios.get('/api/airdrops')
        const data = airdropsRes.data.data || []
        setAirdrops(data)

        // 计算统计数据
        const stats = calculateStats(data)
        setReportData(stats)
      } catch (error) {
        console.error('加载数据失败:', error)
        // 使用模拟数据
        const mockData = generateMockData()
        setAirdrops(mockData)
        setReportData(calculateStats(mockData))
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // 计算统计数据
  function calculateStats(data: Airdrop[]): ReportData {
    const categoryDist: Record<string, number> = {}
    const monthlyTrend: Record<string, number> = {}

    data.forEach(item => {
      // 分类统计
      categoryDist[item.category] = (categoryDist[item.category] || 0) + 1
      
      // 月度趋势
      const month = format(new Date(item.createdAt), 'yyyy-MM')
      monthlyTrend[month] = (monthlyTrend[month] || 0) + 1
    })

    // 计算估算总价值
    const valueMap: Record<string, number> = {
      '$1000-5000': 3000,
      '$500-3000': 1750,
      '$500-2000': 1250,
      '$100-500': 300,
      '$50-200': 125,
      '$50-300': 175
    }
    const totalValue = data.reduce((sum, item) => {
      return sum + (valueMap[item.estimatedValue || ''] || 0)
    }, 0)

    // 模拟最近活动
    const recentActivity = [
      { date: new Date().toISOString(), action: '开始监控', airdrop: 'ZetaChain' },
      { date: subDays(new Date(), 1).toISOString(), action: '完成测试网任务', airdrop: 'LayerZero' },
      { date: subDays(new Date(), 2).toISOString(), action: '添加监控', airdrop: 'Scroll' },
      { date: subDays(new Date(), 3).toISOString(), action: '更新状态', airdrop: 'Arbitrum' },
      { date: subDays(new Date(), 5).toISOString(), action: '开始监控', airdrop: 'Blast' }
    ]

    return {
      totalAirdrops: data.length,
      activeAirdrops: data.filter(d => d.status === 'active').length,
      pendingAirdrops: data.filter(d => d.status === 'pending').length,
      completedAirdrops: data.filter(d => d.status === 'completed').length,
      totalEstimatedValue: `$${totalValue.toLocaleString()}`,
      categoryDistribution: categoryDist,
      monthlyTrend: Object.entries(monthlyTrend).map(([month, count]) => ({ month, count })),
      recentActivity
    }
  }

  // 生成模拟数据
  function generateMockData(): Airdrop[] {
    return [
      { id: '1', name: 'ZetaChain', category: 'Layer1', status: 'active', estimatedValue: '$1000-5000', createdAt: subDays(new Date(), 5).toISOString(), completedTasks: 3, totalTasks: 5 },
      { id: '2', name: 'LayerZero', category: 'Cross-chain', status: 'active', estimatedValue: '$500-2000', createdAt: subDays(new Date(), 10).toISOString(), completedTasks: 4, totalTasks: 6 },
      { id: '3', name: 'Scroll', category: 'Layer2', status: 'active', estimatedValue: '$500-3000', createdAt: subDays(new Date(), 15).toISOString(), completedTasks: 2, totalTasks: 4 },
      { id: '4', name: 'Linea', category: 'Layer2', status: 'pending', estimatedValue: '$500-3000', createdAt: subDays(new Date(), 3).toISOString() },
      { id: '5', name: 'Starknet', category: 'Layer2', status: 'completed', estimatedValue: '$1000-5000', createdAt: subDays(new Date(), 30).toISOString(), completedTasks: 5, totalTasks: 5 },
      { id: '6', name: 'Arbitrum', category: 'Layer2', status: 'completed', estimatedValue: '$1000-5000', createdAt: subDays(new Date(), 45).toISOString(), completedTasks: 4, totalTasks: 4 },
      { id: '7', name: 'Base', category: 'Layer2', status: 'active', estimatedValue: '$500-2000', createdAt: subDays(new Date(), 7).toISOString(), completedTasks: 1, totalTasks: 3 },
      { id: '8', name: 'EigenLayer', category: 'Restaking', status: 'active', estimatedValue: '$500-3000', createdAt: subDays(new Date(), 20).toISOString(), completedTasks: 2, totalTasks: 4 }
    ]
  }

  // 导出报告
  const exportReport = async (exportFormat: 'pdf' | 'excel' | 'csv') => {
    setExporting(true)
    
    try {
      if (exportFormat === 'csv') {
        // 生成 CSV
        const headers = ['项目名称', '分类', '状态', '预估价值', '创建时间', '完成任务', '总任务']
        const rows = airdrops.map(a => [
          a.name,
          a.category,
          a.status,
          a.estimatedValue || 'N/A',
          format(new Date(a.createdAt), 'yyyy-MM-dd'),
          a.completedTasks || 0,
          a.totalTasks || 0
        ])
        
        const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `airdrop-report-${format(new Date(), 'yyyy-MM-dd')}.csv`
        a.click()
      } else {
        // PDF/Excel 导出（模拟）
        alert(`📄 ${exportFormat.toUpperCase()} 导出功能准备中...\n\n将生成包含 ${airdrops.length} 个空投项目的报告`)
      }
      
      setExporting(false)
    } catch (error) {
      console.error('导出失败:', error)
      setExporting(false)
    }
  }

  // 刷新数据
  const refreshData = async () => {
    setLoading(true)
    // 重新加载
    window.location.reload()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载报告中...</p>
        </div>
      </div>
    )
  }

  const categories = Object.entries(reportData?.categoryDistribution || {}).sort((a, b) => b[1] - a[1])

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="hover:text-purple-200 transition-colors">
              ← 返回仪表板
            </Link>
            <span className="text-xl font-bold">|</span>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              空投报告
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={refreshData}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              刷新
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* 统计概览 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">总空投数</p>
                <p className="text-3xl font-bold text-purple-600">{reportData?.totalAirdrops || 0}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <Award className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">进行中</p>
                <p className="text-3xl font-bold text-green-600">{reportData?.activeAirdrops || 0}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">已完成</p>
                <p className="text-3xl font-bold text-blue-600">{reportData?.completedAirdrops || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <TrendingDown className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">预估总价值</p>
                <p className="text-3xl font-bold text-yellow-600">{reportData?.totalEstimatedValue || '$0'}</p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 分类分布 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <PieChart className="w-5 h-5 text-purple-600" />
              分类分布
            </h2>
            <div className="space-y-4">
              {categories.map(([category, count]) => {
                const percentage = ((count / (reportData?.totalAirdrops || 1)) * 100).toFixed(1)
                return (
                  <div key={category}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{category}</span>
                      <span className="text-gray-500">{count} ({percentage}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* 最近活动 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-600" />
              最近活动
            </h2>
            <div className="space-y-4">
              {reportData?.recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start gap-4">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                  <div>
                    <p className="font-medium">{activity.action}</p>
                    <p className="text-sm text-gray-500">{activity.airdrop}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {format(new Date(activity.date), 'MM月dd日 HH:mm')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 空投列表 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-purple-600" />
              空投详情列表
            </h2>
            <div className="flex gap-2">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="week">最近一周</option>
                <option value="month">最近一月</option>
                <option value="all">全部</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">项目名称</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">分类</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">预估价值</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">创建时间</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">完成进度</th>
                </tr>
              </thead>
              <tbody>
                {airdrops.map((airdrop) => (
                  <tr key={airdrop.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{airdrop.name}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                        {airdrop.category}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        airdrop.status === 'active' ? 'bg-green-100 text-green-700' :
                        airdrop.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {airdrop.status === 'active' ? '进行中' : airdrop.status === 'completed' ? '已完成' : '待确认'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-green-600 font-medium">{airdrop.estimatedValue || '-'}</td>
                    <td className="py-3 px-4 text-gray-500">
                      {format(new Date(airdrop.createdAt), 'yyyy-MM-dd')}
                    </td>
                    <td className="py-3 px-4">
                      {airdrop.totalTasks ? (
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${(airdrop.completedTasks! / airdrop.totalTasks) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">
                            {airdrop.completedTasks}/{airdrop.totalTasks}
                          </span>
                        </div>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 导出选项 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Download className="w-5 h-5 text-purple-600" />
            导出报告
          </h2>
          <p className="text-gray-600 mb-4">选择导出格式下载完整报告</p>
          <div className="flex gap-4">
            <button
              onClick={() => exportReport('pdf')}
              disabled={exporting}
              className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              <FileText className="w-5 h-5" />
              PDF
            </button>
            <button
              onClick={() => exportReport('excel')}
              disabled={exporting}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              <BarChart3 className="w-5 h-5" />
              Excel
            </button>
            <button
              onClick={() => exportReport('csv')}
              disabled={exporting}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <Download className="w-5 h-5" />
              CSV
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
