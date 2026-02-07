import axios from 'axios'
import * as cheerio from 'cheerio'

/**
 * Project Website Crawler
 * 用于监控项目官网上的空投信息
 */

interface ProjectConfig {
  name: string
  url: string
  selectors?: {
    announcement?: string
    blog?: string
    medium?: string
  }
}

interface ProjectUpdate {
  title: string
  url: string
  date?: string
  content?: string
}

class ProjectCrawler {
  private defaultSelectors = {
    announcement: 'article, .announcement, .news-item, .blog-post',
    blog: '.blog-list article, .post-list article',
    medium: 'article'
  }

  /**
   * 获取网页内容
   */
  async fetchPage(url: string): Promise<string | null> {
    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        timeout: 10000
      })

      return response.data
    } catch (error) {
      console.error(`获取页面 ${url} 错误:`, error)
      return null
    }
  }

  /**
   * 检测页面中的空投相关信息
   */
  detectAirdropInfo(content: string): { hasAirdrop: boolean; keywords: string[] } {
    const airdropKeywords = [
      'airdrop',
      'token distribution',
      'claiming',
      'snapshot',
      'eligibility',
      'token allocation',
      '空投',
      '代币分发',
      '领取',
      '分配'
    ]

    const $ = cheerio.load(content)
    const text = $('body').text().toLowerCase()
    
    const foundKeywords = airdropKeywords.filter(keyword => 
      text.includes(keyword.toLowerCase())
    )

    return {
      hasAirdrop: foundKeywords.length > 0,
      keywords: foundKeywords
    }
  }

  /**
   * 解析项目更新列表
   */
  parseUpdates(html: string, baseUrl: string, selector?: string): ProjectUpdate[] {
    const $ = cheerio.load(html)
    const updates: ProjectUpdate[] = []
    const elements = $(selector || this.defaultSelectors.announcement)

    elements.each((_, el) => {
      const $el = $(el)
      
      // 获取标题
      const title = $el.find('h1, h2, h3, .title').first().text().trim()
      
      // 获取链接
      const link = $el.find('a').first().attr('href')
      const url = link ? (link.startsWith('http') ? link : new URL(link, baseUrl).href) : ''
      
      // 获取日期
      const date = $el.find('time, .date, .published').attr('datetime') || 
                   $el.find('time, .date, .published').text().trim()

      // 获取内容摘要
      const content = $el.find('p, .excerpt, .summary').first().text().trim()

      if (title && url) {
        updates.push({ title, url, date, content })
      }
    })

    return updates
  }

  /**
   * 监控单个项目
   */
  async monitorProject(config: ProjectConfig): Promise<{
    name: string
    url: string
    hasAirdrop: boolean
    keywords: string[]
    updates: ProjectUpdate[]
  }> {
    const html = await this.fetchPage(config.url)

    if (!html) {
      return {
        name: config.name,
        url: config.url,
        hasAirdrop: false,
        keywords: [],
        updates: []
      }
    }

    // 检测空投信息
    const { hasAirdrop, keywords } = this.detectAirdropInfo(html)

    // 解析更新
    const updates = this.parseUpdates(
      html, 
      config.url, 
      config.selectors?.announcement
    )

    return {
      name: config.name,
      url: config.url,
      hasAirdrop,
      keywords,
      updates: updates.slice(0, 5) // 只返回最近5条更新
    }
  }

  /**
   * 批量监控多个项目
   */
  async monitorProjects(projects: ProjectConfig[]) {
    const results = await Promise.all(
      projects.map(project => this.monitorProject(project))
    )

    // 返回有空投信息的项目
    return results.filter(result => result.hasAirdrop)
  }
}

// 导出单例
export const projectCrawler = new ProjectCrawler()
export default ProjectCrawler
