/**
 * Shared Memory Integration - 记忆互通模块
 *
 * 实现 LobeHub 与 OpenClaw 记忆共享
 */

import { MemoryAdapter, MemoryEntry } from '../core/memory';
import { EventBus, Events } from '../core/event';

export interface SharedMemoryConfig {
  adapter: MemoryAdapter;
  lobehubDir?: string;      // LobeHub 记忆目录
  openclawDir?: string;      // OpenClaw 记忆目录
  syncInterval?: number;     // 同步间隔（毫秒）
  autoSync?: boolean;       // 是否自动同步
}

export class SharedMemoryIntegration {
  private config: SharedMemoryConfig;
  private eventBus: EventBus;
  private syncTimer?: NodeJS.Timeout;
  private unsubscribe?: () => void;

  constructor(config: SharedMemoryConfig, eventBus: EventBus) {
    this.config = {
      syncInterval: 60000,      // 默认 1 分钟
      autoSync: true,
      ...config,
    };
    this.eventBus = eventBus;

    // 监听记忆更新事件
    this.unsubscribe = this.eventBus.subscribe(
      Events.OpenClaw.MEMORY_UPDATED,
      async (event) => {
        await this.syncFromOpenClaw(event.payload);
      }
    );
  }

  /**
   * 启动同步
   */
  start(): void {
    if (this.config.autoSync && this.config.syncInterval > 0) {
      this.syncTimer = setInterval(() => {
        this.sync();
      }, this.config.syncInterval);
    }
  }

  /**
   * 停止同步
   */
  stop(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }

  /**
   * 同步所有来源
   */
  async sync(): Promise<{ lobehub: number; openclaw: number }> {
    const results = { lobehub: 0, openclaw: 0 };

    if (this.config.lobehubDir) {
      results.lobehub = await this.importFromLobeHub();
    }

    if (this.config.openclawDir) {
      results.openclaw = await this.importFromOpenClaw();
    }

    // 发布同步完成事件
    await this.eventBus.publish({
      type: 'memory:sync.complete',
      source: 'shared-memory',
      payload: results,
    });

    return results;
  }

  /**
   * 从 LobeHub 导入记忆
   */
  async importFromLobeHub(): Promise<number> {
    if (!this.config.lobehubDir) return 0;

    const { readdirSync, readFileSync, existsSync } = await import('fs');
    const { join } = await import('path');

    if (!existsSync(this.config.lobehubDir)) return 0;

    let imported = 0;

    try {
      const files = readdirSync(this.config.lobehubDir, { recursive: true })
        .filter((f: string) => f.endsWith('.md'));

      for (const file of files) {
        const filePath = join(this.config.lobehubDir, file as string);
        const content = readFileSync(filePath, 'utf-8');

        // 解析 Markdown 文件
        const entry = this.parseMarkdown(content, 'lobehub');
        if (entry) {
          await this.config.adapter.add(entry);
          imported++;
        }
      }
    } catch (error) {
      console.error('Import from LobeHub error:', error);
    }

    return imported;
  }

  /**
   * 从 OpenClaw 导入记忆
   */
  async importFromOpenClaw(): Promise<number> {
    if (!this.config.openclawDir) return 0;

    const { readdirSync, readFileSync, existsSync } = await import('fs');
    const { join } = await import('path');

    if (!existsSync(this.config.openclawDir)) return 0;

    let imported = 0;

    try {
      // 扫描 OpenClaw memory 目录
      const dirs = ['daily', 'projects'];
      
      for (const dir of dirs) {
        const dirPath = join(this.config.openclawDir, dir);
        if (!existsSync(dirPath)) continue;

        const files = readdirSync(dirPath).filter(f => f.endsWith('.md'));

        for (const file of files) {
          const filePath = join(dirPath, file);
          const content = readFileSync(filePath, 'utf-8');

          // 提取 P 标签行作为记忆
          const entries = this.extractEntries(content, 'openclaw', dir);
          
          for (const entry of entries) {
            await this.config.adapter.add(entry);
            imported++;
          }
        }
      }
    } catch (error) {
      console.error('Import from OpenClaw error:', error);
    }

    return imported;
  }

  /**
   * 添加记忆（自动标注来源）
   */
  async addMemory(
    content: string,
    options: {
      priority: 'P0' | 'P1' | 'P2';
      tags?: string[];
      source: 'lobehub' | 'openclaw' | 'user';
    }
  ): Promise<MemoryEntry> {
    const entry = await this.config.adapter.add({
      content,
      priority: options.priority,
      tags: options.tags || [],
      source: options.source,
    });

    // 发布事件
    await this.eventBus.publish({
      type: 'memory:added',
      source: 'shared-memory',
      payload: { entryId: entry.id, source: options.source },
    });

    return entry;
  }

  /**
   * 搜索记忆
   */
  async search(query: string, options?: {
    priority?: 'P0' | 'P1' | 'P2' | 'all';
    source?: 'lobehub' | 'openclaw' | 'all';
    limit?: number;
  }): Promise<MemoryEntry[]> {
    const result = await this.config.adapter.search({
      query,
      priority: options?.priority || 'all',
      source: options?.source || 'all',
      limit: options?.limit,
    });

    return result.entries;
  }

  /**
   * 获取统计信息
   */
  async getStatus(): Promise<{
    total: number;
    bySource: Record<string, number>;
    syncing: boolean;
    lobehubDir?: string;
    openclawDir?: string;
  }> {
    const count = await this.config.adapter.count();
    
    return {
      total: count.total,
      bySource: count.bySource,
      syncing: !!this.syncTimer,
      lobehubDir: this.config.lobehubDir,
      openclawDir: this.config.openclawDir,
    };
  }

  /**
   * 导出记忆到文件
   */
  async exportToLobeHub(filePath: string): Promise<number> {
    const entries = await this.config.adapter.list({ source: 'lobehub', limit: 1000 });
    
    let content = '# LobeHub Exported Memory\n\n';
    content += `Generated: ${new Date().toISOString()}\n\n`;
    
    for (const entry of entries) {
      content += `## ${entry.priority} - ${entry.createdAt}\n\n`;
      content += `${entry.content}\n\n`;
      content += `Tags: ${entry.tags.join(', ')}\n\n`;
      content += '---\n\n';
    }

    const { writeFileSync } = await import('fs');
    writeFileSync(filePath, content);

    return entries.length;
  }

  // ===== 辅助方法 =====

  private parseMarkdown(content: string, source: string): Omit<MemoryEntry, 'id' | 'createdAt' | 'updatedAt'> | null {
    const lines = content.split('\n');
    
    // 查找 priority 和 tags
    let priority: 'P0' | 'P1' | 'P2' = 'P2';
    let tags: string[] = [];

    for (const line of lines) {
      if (line.toLowerCase().includes('priority:')) {
        const match = line.match(/priority:\s*(P[012])/i);
        if (match) priority = match[1] as 'P0' | 'P1' | 'P2';
      }
      if (line.toLowerCase().includes('tags:')) {
        const match = line.match(/tags:\s*(.+)/i);
        if (match) tags = match[1].split(',').map(t => t.trim());
      }
    }

    // 提取正文
    const bodyStart = content.indexOf('\n\n');
    const body = bodyStart > -1 ? content.slice(bodyStart).trim() : content;

    if (!body) return null;

    return {
      content: body,
      priority,
      tags,
      source: source as 'lobehub' | 'openclaw' | 'user',
    };
  }

  private extractEntries(content: string, source: string, category: string): Omit<MemoryEntry, 'id' | 'createdAt' | 'updatedAt'>[] {
    const entries: Omit<MemoryEntry, 'id' | 'createdAt' | 'updatedAt'>[] = [];
    const lines = content.split('\n');

    let currentEntry: { priority: 'P0' | 'P1' | 'P2'; content: string; date?: string } | null = null;

    for (const line of lines) {
      // 匹配 P 标签
      const match = line.match(/\*?\[(P[012])\]\[(\d{4}-\d{2}-\d{2})\]\*/?/);
      
      if (match) {
        // 保存之前的 entry
        if (currentEntry) {
          entries.push({
            content: currentEntry.content,
            priority: currentEntry.priority,
            tags: [category],
            source: source as 'lobehub' | 'openclaw' | 'user',
          });
        }

        currentEntry = {
          priority: match[1] as 'P0' | 'P1' | 'P2',
          date: match[2],
          content: '',
        };
      } else if (currentEntry && line.trim()) {
        currentEntry.content += line + '\n';
      }
    }

    // 保存最后一个 entry
    if (currentEntry) {
      entries.push({
        content: currentEntry.content.trim(),
        priority: currentEntry.priority,
        tags: [category],
        source: source as 'lobehub' | 'openclaw' | 'user',
      });
    }

    return entries;
  }
}
