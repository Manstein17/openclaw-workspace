import axios from 'axios'

/**
 * Discord Crawler
 * 用于监控 Discord 服务器上的空投信息
 */

interface DiscordConfig {
  botToken: string
  guildId: string
}

interface DiscordMessage {
  id: string
  content: string
  channelId: string
  authorId: string
  authorUsername: string
  createdAt: string
}

class DiscordCrawler {
  private config: DiscordConfig | null = null
  private baseUrl = 'https://discord.com/api/v10'

  constructor(config?: DiscordConfig) {
    if (config) {
      this.config = config
    }
  }

  /**
   * 配置 Bot Token 和服务器 ID
   */
  configure(config: DiscordConfig) {
    this.config = config
  }

  /**
   * 获取请求头
   */
  private getHeaders() {
    if (!this.config?.botToken) {
      throw new Error('Discord Bot Token 未配置')
    }

    return {
      'Authorization': `Bot ${this.config.botToken}`,
      'Content-Type': 'application/json'
    }
  }

  /**
   * 获取频道列表
   */
  async getChannels() {
    try {
      if (!this.config?.guildId) {
        throw new Error('Guild ID 未配置')
      }

      const response = await axios.get(
        `${this.baseUrl}/guilds/${this.config.guildId}/channels`,
        { headers: this.getHeaders() }
      )

      return response.data || []
    } catch (error) {
      console.error('获取频道列表错误:', error)
      return []
    }
  }

  /**
   * 获取频道消息
   */
  async getChannelMessages(channelId: string, limit: number = 100) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/channels/${channelId}/messages`,
        {
          headers: this.getHeaders(),
          params: { limit }
        }
      )

      return response.data || []
    } catch (error) {
      console.error('获取频道消息错误:', error)
      return []
    }
  }

  /**
   * 获取最近消息（跨多个频道）
   */
  async getRecentMessages(channelIds: string[], limit: number = 100): Promise<DiscordMessage[]> {
    const allMessages: DiscordMessage[] = []

    for (const channelId of channelIds) {
      try {
        const messages = await this.getChannelMessages(channelId, limit)
        allMessages.push(...messages.map((msg: any) => ({
          id: msg.id,
          content: msg.content,
          channelId: msg.channel_id,
          authorId: msg.author.id,
          authorUsername: msg.author.username,
          createdAt: msg.timestamp
        })))
      } catch (error) {
        console.error(`获取频道 ${channelId} 消息错误:`, error)
      }
    }

    return allMessages
  }

  /**
   * 检测空投相关关键词
   */
  async detectAirdropMessages(channelIds: string[]): Promise<DiscordMessage[]> {
    const airdropKeywords = [
      'airdrop',
      'claiming',
      'claim',
      'snapshot',
      'eligibility',
      'token distribution',
      '分配',
      '空投',
      '领取'
    ]

    try {
      const messages = await this.getRecentMessages(channelIds, 100)
      
      // 过滤包含空投关键词的消息
      return messages.filter(message => {
        const content = message.content.toLowerCase()
        return airdropKeywords.some(keyword => content.includes(keyword.toLowerCase()))
      })
    } catch (error) {
      console.error('检测空投消息错误:', error)
      return []
    }
  }
}

// 导出单例
export const discordCrawler = new DiscordCrawler()
export default DiscordCrawler
