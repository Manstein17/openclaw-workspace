'use client'

import { useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import axios from 'axios'

function ActivateForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [activationCode, setActivationCode] = useState('')
  const [email, setEmail] = useState(searchParams?.get('email') || '')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await axios.post('/api/activate', {
        email,
        activationCode
      })

      setSuccess(response.data.message || '激活成功！请登录')
      setLoading(false)

      // 3秒后跳转到登录页
      setTimeout(() => {
        router.push('/login')
      }, 3000)
    } catch (err: any) {
      setError(err.response?.data?.error || '激活失败，请检查激活码')
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md">
      {/* Logo */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 glass rounded-2xl mb-4 neon-border">
          <span className="text-4xl">🏆</span>
        </div>
        <h1 className="text-3xl font-bold gradient-text">空投情报局 Pro</h1>
        <p className="text-gray-500 mt-2">激活你的 Pro 会员</p>
      </div>

      {/* 激活表单 */}
      <div className="glass-card p-8">
        <h2 className="text-2xl font-semibold text-white mb-6 text-center">激活会员</h2>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 错误/成功提示 */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 text-red-300 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-500/20 border border-green-500/50 text-green-300 px-4 py-3 rounded-xl text-sm">
              {success}
            </div>
          )}

          {/* 邮箱 */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">邮箱地址</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full input-dark"
              placeholder="your@email.com"
            />
          </div>

          {/* 激活码 */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">激活码</label>
            <input
              type="text"
              value={activationCode}
              onChange={(e) => setActivationCode(e.target.value.toUpperCase())}
              required
              className="w-full input-dark font-mono tracking-wider uppercase"
              placeholder="XXXX-XXXX-XXXX"
            />
          </div>

          {/* 激活按钮 */}
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                激活中...
              </span>
            ) : '激活会员'}
          </button>
        </form>

        {/* 分割线 */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-[#14141e] text-gray-500">或者</span>
          </div>
        </div>

        {/* 登录链接 */}
        <p className="text-center text-gray-500">
          已有账号？{' '}
          <Link href="/login" className="text-purple-400 hover:text-purple-300 font-medium transition-colors">
            立即登录
            </Link>
        </p>
      </div>

      {/* 返回首页 */}
      <p className="text-center mt-6">
        <Link href="/" className="text-gray-500 hover:text-gray-400 text-sm transition-colors">
          ← 返回首页
        </Link>
      </p>
    </div>
  )
}

function Loading() {
  return (
    <div className="w-full max-w-md text-center">
      <div className="inline-flex items-center justify-center w-20 h-20 glass rounded-2xl mb-4 neon-border">
        <span className="text-4xl">🏆</span>
      </div>
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
      <p className="text-gray-500 mt-4">加载中...</p>
    </div>
  )
}

export default function ActivatePage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Suspense fallback={<Loading />}>
        <ActivateForm />
      </Suspense>
    </div>
  )
}
