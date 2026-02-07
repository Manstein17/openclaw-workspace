/**
 * Alerts Page - 设置空投提醒
 * /app/alerts/page.tsx
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Bell, Plus, Trash2, Edit2, Clock, Mail, Smartphone, Check, X, AlertCircle } from 'lucide-react'
import axios from 'axios'

interface Alert {
  id: string
  name: string
  airdropId: string
  airdropName: string
  alertType: 'deadline' | 'news' | 'task' | 'snapshot'
  reminderTime: string
  isEnabled: boolean
  notificationMethod: 'email' | 'browser' | 'telegram'
  createdAt: string
}

export default function AlertsPage() {
  const router = useRouter()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [airdrops, setAirdrops] = useState<{ id: string; name: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingAlert, setEditingAlert] = useState<Alert | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    airdropId: '',
    alertType: 'deadline' as Alert['alertType'],
    reminderTime: '',
    notificationMethod: 'browser' as Alert['notificationMethod']
  })

  // Load alerts and airdrops
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Load alerts
      const alertsRes = await axios.get('/api/alerts')
      if (alertsRes.data.data) {
        setAlerts(alertsRes.data.data)
      } else {
        // Use mock data if no alerts exist
        setAlerts(generateMockAlerts())
      }

      // Load airdrops for dropdown
      const airdropsRes = await axios.get('/api/airdrops')
      if (airdropsRes.data.data) {
        setAirdrops(airdropsRes.data.data.map((a: any) => ({ id: a.id, name: a.name })))
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      setAlerts(generateMockAlerts())
    } finally {
      setLoading(false)
    }
  }

  const generateMockAlerts = (): Alert[] => [
    {
      id: '1',
      name: 'ZetaChain 空投快照提醒',
      airdropId: '1',
      airdropName: 'ZetaChain',
      alertType: 'snapshot',
      reminderTime: '2026-02-15T10:00',
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
      reminderTime: '2026-02-20T18:00',
      isEnabled: true,
      notificationMethod: 'email',
      createdAt: new Date().toISOString()
    },
    {
      id: '3',
      name: 'Scroll 测试网动态提醒',
      airdropId: '3',
      airdropName: 'Scroll',
      alertType: 'news',
      reminderTime: '',
      isEnabled: false,
      notificationMethod: 'telegram',
      createdAt: new Date().toISOString()
    }
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.airdropId || !formData.reminderTime) {
      setMessage({ type: 'error', text: '请填写所有必填字段' })
      return
    }

    const selectedAirdrop = airdrops.find(a => a.id === formData.airdropId)
    const alertName = formData.name || `${selectedAirdrop?.name} 提醒`

    try {
      if (editingAlert) {
        // Update existing alert
        setAlerts(alerts.map(a => 
          a.id === editingAlert.id 
            ? { ...a, ...formData, name: alertName, airdropName: selectedAirdrop?.name || a.airdropName }
            : a
        ))
        setMessage({ type: 'success', text: '✅ 提醒已更新' })
      } else {
        // Create new alert
        const newAlert: Alert = {
          id: Date.now().toString(),
          name: alertName,
          airdropId: formData.airdropId,
          airdropName: selectedAirdrop?.name || 'Unknown',
          alertType: formData.alertType,
          reminderTime: formData.reminderTime,
          isEnabled: true,
          notificationMethod: formData.notificationMethod,
          createdAt: new Date().toISOString()
        }
        setAlerts([...alerts, newAlert])
        setMessage({ type: 'success', text: '✅ 新提醒已创建' })
      }

      setShowForm(false)
      setEditingAlert(null)
      setFormData({
        name: '',
        airdropId: '',
        alertType: 'deadline',
        reminderTime: '',
        notificationMethod: 'browser'
      })
      
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: '操作失败，请重试' })
    }
  }

  const toggleAlert = (id: string) => {
    setAlerts(alerts.map(a => 
      a.id === id ? { ...a, isEnabled: !a.isEnabled } : a
    ))
  }

  const deleteAlert = (id: string) => {
    if (confirm('确定要删除这个提醒吗？')) {
      setAlerts(alerts.filter(a => a.id !== id))
      setMessage({ type: 'success', text: '✅ 提醒已删除' })
      setTimeout(() => setMessage(null), 3000)
    }
  }

  const editAlert = (alert: Alert) => {
    setEditingAlert(alert)
    setFormData({
      name: alert.name,
      airdropId: alert.airdropId,
      alertType: alert.alertType,
      reminderTime: alert.reminderTime.slice(0, 16),
      notificationMethod: alert.notificationMethod
    })
    setShowForm(true)
  }

  const getAlertTypeLabel = (type: Alert['alertType']) => {
    const labels = {
      deadline: '⏰ 截止日期',
      news: '📰 最新消息',
      task: '✅ 任务提醒',
      snapshot: '📸 快照通知'
    }
    return labels[type]
  }

  const getNotificationIcon = (method: Alert['notificationMethod']) => {
    const icons = {
      email: <Mail className="w-4 h-4" />,
      browser: <Bell className="w-4 h-4" />,
      telegram: <Smartphone className="w-4 h-4" />
    }
    return icons[method]
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载提醒中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-white/80 hover:text-white transition-colors">
                ← 返回
              </Link>
              <span className="hidden sm:inline text-white/40">|</span>
              <h1 className="text-xl sm:text-2xl font-bold flex items-center gap-2">
                <Bell className="w-5 h-5 sm:w-6 sm:h-6" />
                <span className="hidden sm:inline">空投提醒</span>
                <span className="sm:hidden">提醒</span>
              </h1>
            </div>
            <button
              onClick={() => { setShowForm(true); setEditingAlert(null); }}
              className="flex items-center gap-2 px-4 py-2 bg-white text-purple-900 rounded-lg font-medium hover:bg-purple-100 transition-colors w-full sm:w-auto justify-center"
            >
              <Plus className="w-4 h-4" />
              添加提醒
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 sm:py-8">
        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message.text}
          </div>
        )}

        {/* Alert Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">{editingAlert ? '编辑提醒' : '添加新提醒'}</h2>
                <button onClick={() => { setShowForm(false); setEditingAlert(null); }} className="text-gray-400 hover:text-gray-600">
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">提醒名称（可选）</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="自定义提醒名称"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">选择项目 *</label>
                  <select
                    value={formData.airdropId}
                    onChange={(e) => setFormData({ ...formData, airdropId: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  >
                    <option value="">请选择空投项目</option>
                    {airdrops.map(airdrop => (
                      <option key={airdrop.id} value={airdrop.id}>{airdrop.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">提醒类型</label>
                  <select
                    value={formData.alertType}
                    onChange={(e) => setFormData({ ...formData, alertType: e.target.value as Alert['alertType'] })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="deadline">⏰ 截止日期提醒</option>
                    <option value="snapshot">📸 快照通知</option>
                    <option value="news">📰 最新消息</option>
                    <option value="task">✅ 任务提醒</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">提醒时间 *</label>
                  <input
                    type="datetime-local"
                    value={formData.reminderTime}
                    onChange={(e) => setFormData({ ...formData, reminderTime: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">通知方式</label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, notificationMethod: 'browser' })}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border transition-colors ${
                        formData.notificationMethod === 'browser' 
                          ? 'bg-purple-100 border-purple-500 text-purple-700' 
                          : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Bell className="w-4 h-4" />
                      <span className="text-sm">浏览器</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, notificationMethod: 'email' })}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border transition-colors ${
                        formData.notificationMethod === 'email' 
                          ? 'bg-purple-100 border-purple-500 text-purple-700' 
                          : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Mail className="w-4 h-4" />
                      <span className="text-sm">邮件</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, notificationMethod: 'telegram' })}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border transition-colors ${
                        formData.notificationMethod === 'telegram' 
                          ? 'bg-purple-100 border-purple-500 text-purple-700' 
                          : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Smartphone className="w-4 h-4" />
                      <span className="text-sm">Telegram</span>
                    </button>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => { setShowForm(false); setEditingAlert(null); }}
                    className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <Check className="w-4 h-4" />
                    {editingAlert ? '更新' : '添加'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6">
            <div className="text-2xl sm:text-3xl font-bold text-purple-600">{alerts.length}</div>
            <div className="text-sm text-gray-500">总提醒数</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6">
            <div className="text-2xl sm:text-3xl font-bold text-green-600">{alerts.filter(a => a.isEnabled).length}</div>
            <div className="text-sm text-gray-500">已启用</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6">
            <div className="text-2xl sm:text-3xl font-bold text-blue-600">{alerts.filter(a => a.notificationMethod === 'browser').length}</div>
            <div className="text-sm text-gray-500">浏览器通知</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6">
            <div className="text-2xl sm:text-3xl font-bold text-orange-600">{alerts.filter(a => a.alertType === 'deadline').length}</div>
            <div className="text-sm text-gray-500">截止提醒</div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-4 sm:p-6 border-b">
            <h2 className="text-lg sm:text-xl font-semibold flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-600" />
              我的提醒
            </h2>
          </div>

          {alerts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Bell className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>还没有设置任何提醒</p>
              <p className="text-sm mt-2">点击右上角按钮添加第一个提醒</p>
            </div>
          ) : (
            <div className="divide-y">
              {alerts.map((alert) => (
                <div key={alert.id} className="p-4 sm:p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
                        alert.isEnabled ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                        {getNotificationIcon(alert.notificationMethod)}
                      </div>
                      <div>
                        <h3 className="font-medium text-lg">{alert.name}</h3>
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                            {alert.airdropName}
                          </span>
                          <span className="text-sm text-gray-500">{getAlertTypeLabel(alert.alertType)}</span>
                        </div>
                        {alert.reminderTime && (
                          <div className="flex items-center gap-1 mt-2 text-sm text-gray-600">
                            <Clock className="w-4 h-4" />
                            {new Date(alert.reminderTime).toLocaleString('zh-CN')}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 sm:ml-4">
                      <button
                        onClick={() => toggleAlert(alert.id)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          alert.isEnabled ? 'bg-green-500' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            alert.isEnabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                      
                      <button
                        onClick={() => editAlert(alert)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="编辑"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => deleteAlert(alert.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Notification Info */}
        <div className="mt-8 bg-blue-50 rounded-xl p-4 sm:p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-blue-700">通知说明</h3>
              <ul className="text-sm text-blue-600 mt-2 space-y-1">
                <li>• 浏览器通知需要在浏览器中授权才能收到</li>
                <li>• 邮件通知需要先绑定邮箱账号</li>
                <li>• Telegram通知需要先连接Telegram账号</li>
                <li>• 提醒会在设定时间前30分钟和5分钟发送通知</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
