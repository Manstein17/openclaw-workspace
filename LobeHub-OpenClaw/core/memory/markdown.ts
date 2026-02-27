/**
 * Markdown Memory Adapter - Markdown 文件记忆适配器
 *
 * 基于文件系统的记忆存储，与 OpenClaw 兼容
 */

import * as fs from 'fs';
import * as path from 'path';
import { MemoryAdapter, MemoryEntry, MemoryQuery, MemoryResult } from './index';

export class MarkdownMemoryAdapter implements MemoryAdapter {
  name = 'markdown';
  private memoryDir: string;

  constructor(options: { memoryDir: string }) {
    this.memoryDir = options.memoryDir;
    this.ensureDir();
  }

  private ensureDir(): void {
    if (!fs.existsSync(this.memoryDir)) {
      fs.mkdirSync(this.memoryDir, { recursive: true });
    }
  }

  /**
   * 添加记忆条目
   */
  async add(entry: Omit<MemoryEntry, 'id' | 'createdAt' | 'updatedAt'>): Promise<MemoryEntry> {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    
    const fullEntry: MemoryEntry = {
      ...entry,
      id,
      createdAt: now,
      updatedAt: now,
    };

    // 根据 source 保存到对应目录
    const sourceDir = path.join(this.memoryDir, entry.source);
    if (!fs.existsSync(sourceDir)) {
      fs.mkdirSync(sourceDir, { recursive: true });
    }

    const priorityDir = path.join(sourceDir, entry.priority);
    if (!fs.existsSync(priorityDir)) {
      fs.mkdirSync(priorityDir, { recursive: true });
    }

    const filePath = path.join(priorityDir, `${id}.md`);
    const content = this.formatEntry(fullEntry);
    
    fs.writeFileSync(filePath, content);

    return fullEntry;
  }

  /**
   * 获取单条记忆
   */
  async get(id: string): Promise<MemoryEntry | null> {
    // 遍历搜索
    const entries = await this.scanAll();
    return entries.find(e => e.id === id) || null;
  }

  /**
   * 更新记忆
   */
  async update(id: string, content: string): Promise<MemoryEntry | null> {
    const entry = await this.get(id);
    if (!entry) return null;

    entry.content = content;
    entry.updatedAt = new Date().toISOString();

    const filePath = await this.findFile(id);
    if (filePath) {
      fs.writeFileSync(filePath, this.formatEntry(entry));
    }

    return entry;
  }

  /**
   * 删除记忆
   */
  async delete(id: string): Promise<boolean> {
    const filePath = await this.findFile(id);
    if (filePath) {
      fs.unlinkSync(filePath);
      return true;
    }
    return false;
  }

  /**
   * 搜索记忆
   */
  async search(query: MemoryQuery): Promise<MemoryResult> {
    const entries = await this.scanAll();
    let filtered = entries;

    // 按 priority 过滤
    if (query.priority && query.priority !== 'all') {
      filtered = filtered.filter(e => e.priority === query.priority);
    }

    // 按 source 过滤
    if (query.source && query.source !== 'all') {
      filtered = filtered.filter(e => e.source === query.source);
    }

    // 按 tags 过滤
    if (query.tags && query.tags.length > 0) {
      filtered = filtered.filter(e => 
        query.tags!.some(t => e.tags.includes(t))
      );
    }

    // 简单关键词匹配（后续可接入向量搜索）
    if (query.query) {
      const lowerQuery = query.query.toLowerCase();
      filtered = filtered.filter(e => 
        e.content.toLowerCase().includes(lowerQuery) ||
        e.tags.some(t => t.toLowerCase().includes(lowerQuery))
      );
    }

    // 限制数量
    const limit = query.limit || 20;
    const result = filtered.slice(0, limit);

    return {
      entries: result,
      total: filtered.length,
    };
  }

  /**
   * 列出记忆
   */
  async list(options?: { 
    source?: string; 
    tags?: string[]; 
    limit?: number;
    priority?: string;
  }): Promise<MemoryEntry[]> {
    let entries = await this.scanAll();

    if (options?.source && options.source !== 'all') {
      entries = entries.filter(e => e.source === options.source);
    }

    if (options?.priority) {
      entries = entries.filter(e => e.priority === options.priority);
    }

    if (options?.tags && options.tags.length > 0) {
      entries = entries.filter(e => 
        options.tags!.some(t => e.tags.includes(t))
      );
    }

    if (options?.limit) {
      entries = entries.slice(0, options.limit);
    }

    return entries;
  }

  /**
   * 清空记忆
.slice(0,   */
  async clear(source?: string): Promise<number> {
    let count = 0;
    const dirsToClear = source 
      ? [path.join(this.memoryDir, source)]
      : [this.memoryDir];

    for (const dir of dirsToClear) {
      if (fs.existsSync(dir)) {
        const files = this.getAllFiles(dir);
        files.forEach(f => {
          fs.unlinkSync(f);
          count++;
        });
      }
    }

    return count;
  }

  /**
   * 统计
   */
  async count(): Promise<{ total: number; bySource: Record<string, number> }> {
    const entries = await this.scanAll();
    const bySource: Record<string, number> = {};

    entries.forEach(e => {
      bySource[e.source] = (bySource[e.source] || 0) + 1;
    });

    return { total: entries.length, bySource };
  }

  // ===== 辅助方法 =====

  private async scanAll(): Promise<MemoryEntry[]> {
    if (!fs.existsSync(this.memoryDir)) return [];

    const files = this.getAllFiles(this.memoryDir);
    const entries: MemoryEntry[] = [];

    for (const file of files) {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        const entry = this.parseEntry(content, file);
        if (entry) entries.push(entry);
      } catch {
        // 忽略读取错误
      }
    }

    return entries;
  }

  private getAllFiles(dir: string): string[] {
    if (!fs.existsSync(dir)) return [];
    
    const files: string[] = [];
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.getAllFiles(fullPath));
      } else if (item.endsWith('.md')) {
        files.push(fullPath);
      }
    }

    return files;
  }

  private async findFile(id: string): Promise<string | null> {
    const files = this.getAllFiles(this.memoryDir);
    return files.find(f => f.includes(id)) || null;
  }

  private formatEntry(entry: MemoryEntry): string {
    return `---
id: ${entry.id}
priority: ${entry.priority}
created: ${entry.createdAt}
updated: ${entry.updatedAt}
tags: ${entry.tags.join(', ')}
source: ${entry.source}
---

${entry.content}`;
  }

  private parseEntry(content: string, filePath: string): MemoryEntry | null {
    const lines = content.split('\n');
    const frontmatterEnd = lines.findIndex(l => l.trim() === '---');
    
    if (frontmatterEnd === -1) return null;

    const frontmatter = lines.slice(0, frontmatterEnd).join('\n');
    const body = lines.slice(frontmatterEnd + 1).join('\n').trim();

    const meta: Record<string, any> = {};
    frontmatter.split('\n').forEach(line => {
      const [key, ...value] = line.split(':');
      if (key && value) {
        meta[key.trim()] = value.join(':').trim();
      }
    });

    return {
      id: meta.id || '',
      content: body,
      priority: (meta.priority as 'P0' | 'P1' | 'P2') || 'P2',
      createdAt: meta.created || new Date().toISOString(),
      updatedAt: meta.updated || new Date().toISOString(),
      tags: meta.tags ? meta.tags.split(',').map((t: string) => t.trim()) : [],
      source: (meta.source as 'lobehub' | 'openclaw' | 'user') || 'user',
    };
  }
}
