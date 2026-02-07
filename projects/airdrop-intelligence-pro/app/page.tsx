import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold">
            🏆 空投情报局 Pro
          </Link>
          <div className="flex gap-4 items-center">
            <Link href="/pricing" className="text-gray-300 hover:text-white">
              价格
            </Link>
            <Link href="/login" className="btn-primary text-sm px-4 py-2">
              登录
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 pt-24">
        <div className="container mx-auto px-4">
          {/* Hero Content */}
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 glass rounded-full text-sm text-purple-300 mb-6">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              实时监控中 · 已发现 500+ 空投项目
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="gradient-text">🏆 空投情报局</span>
              <span className="text-white"> Pro</span>
            </h1>
            
            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto leading-relaxed">
              帮你找到 + 筛选 + 指导操作空投机会
              <br />
              <span className="text-purple-400">专业空投资讯监控与提醒服务</span>
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center gap-4 mb-12">
              <Link href="/dashboard" className="btn-primary text-lg px-8 py-4">
                🚀 免费试用
              </Link>
              <Link href="/pricing" className="btn-secondary text-lg px-8 py-4">
                💰 查看价格
              </Link>
            </div>
            
            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 max-w-lg mx-auto">
              <div className="glass-card p-4">
                <div className="text-3xl font-bold gradient-text">500+</div>
                <div className="text-sm text-gray-500">监控项目</div>
              </div>
              <div className="glass-card p-4">
                <div className="text-3xl font-bold gradient-text">1000+</div>
                <div className="text-sm text-gray-500">活跃用户</div>
              </div>
              <div className="glass-card p-4">
                <div className="text-3xl font-bold gradient-text">¥500K+</div>
                <div className="text-sm text-gray-500">帮助赚取</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-4">
            😰 <span className="gradient-text">撸毛人的痛点</span>
          </h2>
          <p className="text-gray-500 text-center mb-12">你是否也有这些困扰？</p>
          
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {[
              { icon: '⏰', title: '信息过载', desc: 'Twitter、Discord、Telegram 消息太多，根本看不过来，错过重要机会' },
              { icon: '🔍', title: '筛选困难', desc: '不知道哪些是真的空投，哪些是骗子，浪费时间在无效项目上' },
              { icon: '📝', title: '操作复杂', desc: '找到空投也不会做，英语不好，看不懂教程，错过最佳时机' },
              { icon: '😫', title: '时间不够', desc: '每天花几小时刷信息，没时间做其他事情，身体被掏空' },
            ].map((item, i) => (
              <div key={i} className="glass-card p-6 card-hover">
                <div className="text-4xl mb-4">{item.icon}</div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core Value Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-4">
            💎 <span className="gradient-text">我们的核心价值</span>
          </h2>
          <p className="text-xl text-gray-400 text-center mb-12 max-w-3xl mx-auto">
            不只是工具，更是你的「空投军师」<br />
            帮你用 <span className="text-cyan-400">10%</span> 的时间，赚 <span className="text-purple-400">80%</span> 的收益
          </p>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* AI 自动化 */}
            <div className="glass-card p-8 card-hover neon-border">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-3xl mb-6">
                🤖
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">AI 自动化</h3>
              <p className="text-gray-400 mb-6">7x24 小时自动监控，AI 智能筛选，不让你错过任何机会</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-center gap-2">
                  <span className="text-cyan-400">✓</span> 500+ 项目实时监控
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-cyan-400">✓</span> AI 去重 + 去噪
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-cyan-400">✓</span> 关键词智能匹配
                </li>
              </ul>
            </div>

            {/* 精准筛选 */}
            <div className="glass-card p-8 card-hover neon-border">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center text-3xl mb-6">
                🎯
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">精准筛选</h3>
              <p className="text-gray-400 mb-6">只推高价值空投，帮你过滤 90% 垃圾信息，命中率提升 300%</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-center gap-2">
                  <span className="text-pink-400">✓</span> 风险等级自动评估
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-pink-400">✓</span> 价值排名筛选
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-pink-400">✓</span> 项目质量评分
                </li>
              </ul>
            </div>

            {/* 手把手教程 */}
            <div className="glass-card p-8 card-hover neon-border">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-green-500 flex items-center justify-center text-3xl mb-6">
                📚
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">手把手教程</h3>
              <p className="text-gray-400 mb-6">保姆级中文教程，小白也能学会，让空投变得简单</p>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span> 每步都有截图说明
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span> 中文教程无障碍
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-400">✓</span> 进度追踪提醒
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Competitive Advantage */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="glass-card p-12 max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-4">
              ⚔️ <span className="gradient-text">核心竞争力</span>
            </h2>
            <p className="text-xl text-gray-400 text-center mb-12">区别于其他工具，我们不只是信息的搬运工</p>
            
            <div className="grid md:grid-cols-2 gap-8">
              {[
                { num: '1', title: '不仅仅是监控', desc: '市面上很多工具只能监控，我们提供「监控 + 筛选 + 教程」一站式服务', sub: '别人给你 100 条信息，我们帮你精选 5 条有价值的', color: 'text-purple-400' },
                { num: '2', title: '垂直深耕', desc: '我们只做空投一件事，把这一件事做到极致', sub: '不做泛财经，不做大而全，只做空投细分领域第一', color: 'text-cyan-400' },
                { num: '3', title: '持续进化', desc: 'AI 不断学习，项目库持续更新，帮你发现更多机会', sub: '我们的系统在成长，你的收益也在增长', color: 'text-green-400' },
                { num: '4', title: '社群陪伴', desc: '不只是工具，有温度的社群，陪你一起成长', sub: '赚钱路上不孤单，一群志同道合的朋友陪你', color: 'text-pink-400' },
              ].map((item, i) => (
                <div key={i} className="flex gap-6 items-start">
                  <div className={`text-5xl font-bold ${item.color} opacity-50`}>{item.num}</div>
                  <div>
                    <h3 className={`text-xl font-bold mb-2 ${item.color}`}>{item.title}</h3>
                    <p className="text-gray-300 mb-1">{item.desc}</p>
                    <p className="text-sm text-gray-500">{item.sub}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">
            📊 <span className="gradient-text">竞品对比</span>
          </h2>
          
          <div className="overflow-x-auto max-w-4xl mx-auto">
            <table className="w-full table-dark">
              <thead>
                <tr>
                  <th className="py-4 px-6 text-left">功能</th>
                  <th className="py-4 px-6 text-center text-purple-400">空投情报局 Pro</th>
                  <th className="py-4 px-6 text-center text-gray-500">其他监控工具</th>
                  <th className="py-4 px-6 text-center text-gray-500">付费社群</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['AI 智能筛选', '✅ 独家', '❌ 无', '❌ 无'],
                  ['操作教程', '✅ 手把手中文', '❌ 无', '⚠️ 偶尔'],
                  ['实时推送', '✅ 多种渠道', '⚠️ 单一', '⚠️ 延迟'],
                  ['项目评估', '✅ AI 评分', '❌ 无', '⚠️ 主观'],
                  ['价格/月', '¥29', '$50+', '¥99+'],
                ].map((row, i) => (
                  <tr key={i} className="border-b border-white/5">
                    <td className="py-4 px-6 text-gray-300">{row[0]}</td>
                    <td className="py-4 px-6 text-center text-green-400 font-semibold">{row[1]}</td>
                    <td className="py-4 px-6 text-center text-gray-500">{row[2]}</td>
                    <td className="py-4 px-6 text-center text-gray-500">{row[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="glass-card p-12 text-center neon-border">
            <h2 className="text-4xl font-bold mb-6">
              💎 <span className="gradient-text">你能获得什么</span>
            </h2>
            <p className="text-xl text-gray-400 mb-12 max-w-3xl mx-auto">
              投资自己，投资知识，获得持续的被动收入能力
            </p>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              <div className="glass p-6 rounded-2xl">
                <div className="text-5xl mb-4">⏰</div>
                <h3 className="text-xl font-bold text-white mb-2">省时间</h3>
                <p className="text-gray-400">
                  每天省下 3-5 小时<br />
                  <span className="text-sm text-gray-500">(每年省下 1000+ 小时)</span>
                </p>
              </div>
              
              <div className="glass p-6 rounded-2xl">
                <div className="text-5xl mb-4">💰</div>
                <h3 className="text-xl font-bold text-white mb-2">赚收益</h3>
                <p className="text-gray-400">
                  1-2 个空投 = 月卡回本<br />
                  <span className="text-sm text-gray-500">(历史数据证明可行)</span>
                </p>
              </div>
              
              <div className="glass p-6 rounded-2xl">
                <div className="text-5xl mb-4">🧠</div>
                <h3 className="text-xl font-bold text-white mb-2">涨知识</h3>
                <p className="text-gray-400">
                  学会空投底层逻辑<br />
                  <span className="text-sm text-gray-500">(终身受用的技能)</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Preview */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-4">
            💰 <span className="gradient-text">灵活定价</span>
          </h2>
          <p className="text-center text-gray-400 mb-12">根据你的需求选择合适的方案</p>
          
          <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {/* 体验卡 */}
            <div className="glass-card p-6 card-hover">
              <h3 className="text-lg font-semibold text-gray-400 text-center">体验卡</h3>
              <div className="text-4xl font-bold my-4 text-center text-white">¥9.9</div>
              <p className="text-sm text-gray-500 text-center mb-4">7天有效</p>
              <ul className="text-sm space-y-3 text-gray-400 mb-6">
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 基础空投发现</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 每日简报</li>
                <li className="flex items-center gap-2"><span className="text-gray-600">×</span> 无实时推送</li>
                <li className="flex items-center gap-2"><span className="text-gray-600">×</span> 无操作指南</li>
              </ul>
              <Link href="/pricing" className="block w-full py-2 text-center border border-gray-600 rounded-lg hover:border-purple-500 transition-colors text-gray-300">
                了解更多
              </Link>
            </div>

            {/* 月卡 - 推荐 */}
            <div className="glass-card p-6 card-hover neon-border relative transform scale-105 shadow-xl">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-1 rounded-full text-sm">
                最推荐
              </div>
              <h3 className="text-lg font-semibold text-purple-400 text-center">月卡</h3>
              <div className="text-4xl font-bold my-4 text-center gradient-text">¥29</div>
              <p className="text-sm text-gray-500 text-center mb-4">30天有效</p>
              <ul className="text-sm space-y-3 text-gray-400 mb-6">
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 全部空投发现</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 实时推送</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 操作指南</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 社群支持</li>
              </ul>
              <Link href="/pricing" className="btn-primary block w-full text-center">
                立即购买
              </Link>
            </div>

            {/* 季卡 */}
            <div className="glass-card p-6 card-hover">
              <h3 className="text-lg font-semibold text-gray-400 text-center">季卡</h3>
              <div className="text-4xl font-bold my-4 text-center text-white">¥79</div>
              <p className="text-sm text-gray-500 text-center mb-4">90天有效</p>
              <ul className="text-sm space-y-3 text-gray-400 mb-6">
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 全部功能</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 优先支持</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 专属社群</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 额外福利</li>
              </ul>
              <Link href="/pricing" className="block w-full py-2 text-center border border-gray-600 rounded-lg hover:border-cyan-500 transition-colors text-gray-300">
                节省 9%
              </Link>
            </div>

            {/* 年卡 */}
            <div className="glass-card p-6 card-hover">
              <h3 className="text-lg font-semibold text-gray-400 text-center">年卡</h3>
              <div className="text-4xl font-bold my-4 text-center text-white">¥199</div>
              <p className="text-sm text-gray-500 text-center mb-4">365天有效</p>
              <ul className="text-sm space-y-3 text-gray-400 mb-6">
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 全部功能</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 最高优先级</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 专属客服</li>
                <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 未来产品免费</li>
              </ul>
              <Link href="/pricing" className="block w-full py-2 text-center border border-gray-600 rounded-lg hover:border-green-500 transition-colors text-gray-300">
                节省 43%
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">
            ❓ <span className="gradient-text">常见问题</span>
          </h2>
          
          <div className="max-w-3xl mx-auto space-y-4">
            {[
              { q: '空投真的能赚钱吗？', a: '是的。根据历史数据，做好一个顶级空投可赚 $100-$5000 不等。月卡 ¥29，赚 1 个普通空投就回本。' },
              { q: '需要很多时间吗？', a: '不需要。我们帮你节省 90% 筛选时间，每天只需 10-30 分钟完成操作。' },
              { q: '小白能学会吗？', a: '当然可以。我们提供手把手中文教程，每一步都有截图说明。' },
              { q: '会不会是骗子？', a: '我们只筛选正规项目，避开土狗和骗局。但投资有风险，建议 DYOR。' },
            ].map((item, i) => (
              <div key={i} className="glass-card p-6">
                <h3 className="font-semibold text-white mb-2">Q: {item.q}</h3>
                <p className="text-gray-400">A: {item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="glass-card p-12 text-center neon-border max-w-3xl mx-auto">
            <h2 className="text-4xl font-bold mb-4">
              🚀 <span className="gradient-text">开始你的空投之旅</span>
            </h2>
            <p className="text-xl text-gray-400 mb-8">
              每个月花一顿饭的钱，赚回 10 倍的收益
            </p>
            
            <Link href="/dashboard" className="btn-primary text-lg px-8 py-4 inline-block">
              免费试用
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="text-xl font-bold mb-4 gradient-text">🏆 空投情报局 Pro</h3>
              <p className="text-gray-500 text-sm">帮你找到 + 筛选 + 指导操作空投机会</p>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-4">快速链接</h4>
              <ul className="space-y-2 text-gray-500 text-sm">
                <li><Link href="/dashboard" className="hover:text-purple-400 transition-colors">首页</Link></li>
                <li><Link href="/pricing" className="hover:text-purple-400 transition-colors">价格方案</Link></li>
                <li><Link href="/login" className="hover:text-purple-400 transition-colors">登录</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-4">联系我们</h4>
              <p className="text-gray-500 text-sm">
                Telegram: @airdrop_bureau<br />
                邮箱: support@airdrop.pro
              </p>
            </div>
          </div>
          
          <div className="border-t border-white/5 pt-8 text-center text-gray-600 text-sm">
            <p>© 2026 空投情报局 Pro. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
