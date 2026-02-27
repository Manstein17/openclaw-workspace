/**
 * Qdrant Memory Adapter - Qdrant 向量数据库适配器
 *
 * 提供语义搜索能力
 */

import { MemoryAdapter, MemoryEntry, MemoryQuery, MemoryResult } from './index';

interface QdrantConfig {
  url?: string;
  apiKey?: string;
  collectionName?: string;
}

export class QdrantMemoryAdapter implements MemoryAdapter {
  name = 'qdrant';
  private config: QdrantConfig;
  private baseUrl: string;
  private collection: string;

  constructor(config: QdrantConfig = {}) {
    this.config = config;
    this.baseUrl = config.url || process.env.QDRANT_URL || 'http://localhost:6333';
    this.collection = config.collectionName || 'lobehub-openclaw-memory';
  }

  async add(entry: Omit<MemoryEntry, 'id' | 'createdAt' | 'updatedAt'>): Promise<MemoryEntry> {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    
    const fullEntry: MemoryEntry = {
      ...entry,
      id,
      createdAt: now,
      updatedAt: now,
    };

    // 生成向量嵌入（需要调用嵌入模型 API）
    const vector = await this.generateEmbedding(entry.content);

    const payload = {
      content: entry.content,
      priority: entry.priority,
      tags: entry.tags,
      source: entry.source,
      createdAt: now,
      updatedAt: now,
    };

    try {
      await fetch(`${this.baseUrl}/collections/${this.collection}/points`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
        },
        body: JSON.stringify({
          points: [{
            id,
            payload,
            vector,
          }],
        }),
      });
    } catch (error) {
      console.error('Qdrant add error:', error);
    }

    return fullEntry;
  }

  async get(id: string): Promise<MemoryEntry | null> {
    try {
      const response = await fetch(
        `${this.baseUrl}/collections/${this.collection}/points/${id}`,
        {
          headers: {
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
        }
      );
      
      if (!response.ok) return null;
      
      const data = await response.json();
      const result = data.result;
      
      return {
        id,
        content: result.payload.content,
        priority: result.payload.priority,
        createdAt: result.payload.createdAt,
        updatedAt: result.payload.updatedAt,
        tags: result.payload.tags,
        source: result.payload.source,
      };
    } catch {
      return null;
    }
  }

  async update(id: string, content: string): Promise<MemoryEntry | null> {
    const entry = await this.get(id);
    if (!entry) return null;

    const vector = await this.generateEmbedding(content);
    const now = new Date().toISOString();

    try {
      await fetch(
        `${this.baseUrl}/collections/${this.collection}/points/${id}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
          body: JSON.stringify({
            payload: {
              content,
              updatedAt: now,
            },
          }),
        }
      );
    } catch (error) {
      console.error('Qdrant update error:', error);
    }

    return { ...entry, content, updatedAt: now };
  }

  async delete(id: string): Promise<boolean> {
    try {
      const response = await fetch(
        `${this.baseUrl}/collections/${this.collection}/points/${id}`,
        {
          method: 'DELETE',
          headers: {
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
        }
      );
      return response.ok;
    } catch {
      return false;
    }
  }

  async search(query: MemoryQuery): Promise<MemoryResult> {
    const queryVector = await this.generateEmbedding(query.query);
    const limit = query.limit || 20;

    try {
      const searchBody: any = {
        params: { limit },
        vector: queryVector,
      };

      // 添加过滤条件
      const must: any[] = [];
      
      if (query.priority && query.priority !== 'all') {
        must.push({ key: 'priority', match: { value: query.priority } });
      }

      if (query.source && query.source !== 'all') {
        must.push({ key: 'source', match: { value: query.source } });
      }

      if (query.tags && query.tags.length > 0) {
        must.push({
          key: 'tags',
          match: { any: query.tags },
        });
      }

      if (must.length > 0) {
        searchBody.filter = { must };
      }

      const response = await fetch(
        `${this.baseUrl}/collections/${this.collection}/points/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
          body: JSON.stringify(searchBody),
        }
      );

      if (!response.ok) {
        return { entries: [], total: 0 };
      }

      const data = await response.json();
      const results = data.result?.result || [];

      const entries: MemoryEntry[] = results.map((r: any) => ({
        id: r.id,
        content: r.payload.content,
        priority: r.payload.priority,
        createdAt: r.payload.createdAt,
        updatedAt: r.payload.updatedAt,
        tags: r.payload.tags,
        source: r.payload.source,
      }));

      return { entries, total: entries.length };
    } catch (error) {
      console.error('Qdrant search error:', error);
      return { entries: [], total: 0 };
    }
  }

  async list(options?: { 
    source?: string; 
    tags?: string[]; 
    limit?: number;
    priority?: string;
  }): Promise<MemoryEntry[]> {
    // 使用 scroll API 获取所有点
    try {
      const scrollBody: any = { limit: options?.limit || 100 };
      
      const must: any[] = [];
      if (options?.source) {
        must.push({ key: 'source', match: { value: options.source } });
      }
      if (options?.priority) {
        must.push({ key: 'priority', match: { value: options.priority } });
      }
      if (options?.tags && options.tags.length > 0) {
        must.push({ key: 'tags', match: { any: options.tags } });
      }

      if (must.length > 0) {
        scrollBody.filter = { must };
      }

      const response = await fetch(
        `${this.baseUrl}/collections/${this.collection}/points/scroll`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
          body: JSON.stringify(scrollBody),
        }
      );

      if (!response.ok) return [];

      const data = await response.json();
      const results = data.result?.result || [];

      return results.map((r: any) => ({
        id: r.id,
        content: r.payload.content,
        priority: r.payload.priority,
        createdAt: r.payload.createdAt,
        updatedAt: r.payload.updatedAt,
        tags: r.payload.tags,
        source: r.payload.source,
      }));
    } catch {
      return [];
    }
  }

  async clear(source?: string): Promise<number> {
    // 删除符合条件的点
    try {
      const must: any[] = [];
      if (source) {
        must.push({ key: 'source', match: { value: source } });
      }

      const response = await fetch(
        `${this.baseUrl}/collections/${this.collection}/points/delete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
          body: JSON.stringify({
            filter: must.length > 0 ? { must } : undefined,
          }),
        }
      );

      if (!response.ok) return 0;
      
      const data = await response.json();
      return data.result?.deleted || 0;
    } catch {
      return 0;
    }
  }

  async count(): Promise<{ total: number; bySource: Record<string, number> }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/collections/${this.collection}`,
        {
          headers: {
            ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
          },
        }
      );

      if (!response.ok) return { total: 0, bySource: {} };

      const data = await response.json();
      return { total: data.result?.points_count || 0, bySource: {} };
    } catch {
      return { total: 0, bySource: {} };
    }
  }

  /**
   * 初始化集合
   */
  async initCollection(): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/collections/${this.collection}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vectors: {
            size: 384,
            distance: 'Cosine',
          },
        }),
      });
    } catch (error) {
      console.error('Qdrant init error:', error);
    }
  }

  /**
   * 生成向量嵌入
   */
  private async generateEmbedding(text: string): Promise<number[]> {
    // TODO: 接入嵌入模型（OpenAI / HuggingFace / Ollama）
    // 这里返回随机向量作为占位符
    const embedding: number[] = [];
    for (let i = 0; i < 384; i++) {
      embedding.push(Math.random() * 2 - 1);
    }
    return embedding;
  }
}
