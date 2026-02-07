import axios from 'axios'

/**
 * Twitter Crawler
 * 用于监控 Twitter/X 上的空投信息
 */

interface TwitterConfig {
  apiKey: string
  apiSecret: string
  accessToken: string
  accessSecret: string
}

interface Tweet {
  id: string
  text: string
  createdAt: string
  authorId: string
  authorUsername: string
}

class TwitterCrawler {
  private config: TwitterConfig | null = null
  private baseUrl = 'https://api.twitter.com/2'

  constructor(config?: TwitterConfig) {
    if (config) {
      this.config = config
    }
  }

  /**
   * 配置 API 密钥
   */
  configure(config: TwitterConfig) {
    this.config = config
  }

  /**
   * 生成 Bearer Token（简化版）
   * 实际项目中应该使用 OAuth 2.0 或应用-only authentication
   */
  private getHeaders() {
    if (!this.config) {
      throw new Error('Twitter API 未配置')
    }

    return {
      'Authorization': `Bearer ${this.config.apiKey}`,
      'Content-Type': 'application/json'
    }
  }

  /**
   * 获取用户推文
   */
  async getUserTweets(userId: string, maxResults: number = 100): Promise<Tweet[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/users/${userId}/tweets`, {
        headers: this.getHeaders(),
        params: {
          max_results: maxResults,
          'tweet.fields': 'createdAt,author_id'
        }
      })

      return response.data.data || []
    } catch (error) {
      console.error('获取推文错误:', error)
      return []
    }
  }

  /**
   * 搜索推文
   */
  async searchTweets(query: string, maxResults: number = 100): Promise<Tweet[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/tweets/search/recent`, {
        headers: this.getHeaders(),
        params: {
          query,
          max_results: maxResults,
          'tweet.fields': 'createdAt,author_id'
        }
      })

      return response.data.data || []
    } catch (error) {
      console.error('搜索推文错误:', error)
      return []
    }
  }

  /**
   * 检测空投相关关键词
   */
  async detectAirdropTweets(userId: string): Promise<Tweet[]> {
    const airdropKeywords = [
      'airdrop',
      '$AIRDROP',
      'claiming',
      'claim token',
      'snapshot',
      'eligibility',
      '分配',
      '空投'
    ]

    try {
      const tweets = await this.getUserTweets(userId, 100)
      
      // 过滤包含空投关键词的推文
      return tweets.filter(tweet => {
        const text = tweet.text.toLowerCase()
        return airdropKeywords.some(keyword => text.includes(keyword.toLowerCase()))
      })
    } catch (error) {
      console.error('检测空投推文错误:', error)
      return []
    }
  }
}

// 导出单例
export const twitterCrawler = new TwitterCrawler()
export default TwitterCrawler
