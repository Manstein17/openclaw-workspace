/**
 * Unified Memory Interface - 统一记忆接口
 *
 * 提供统一记忆操作抽象，支持 LobeHub 与 OpenClaw 记忆互通
 */

export interface MemoryEntry {
  id: string;
  content: string;
  priority: 'P0' | 'P1' | 'P2';
  createdAt: string;
  updatedAt: string;
  tags: string[];
  source: 'lobehub' | 'openclaw' | 'user';
  metadata?: Record<string, any>;
}

export interface MemoryQuery {
  query: string;
  tags?: string[];
  priority?: 'P0' | 'P1' | 'P2' | 'all';
  limit?: number;
  source?: 'lobehub' | 'openclaw' | 'all';
}

export interface MemoryResult {
  entries: MemoryEntry[];
  total: number;
}

export interface MemoryAdapter {
  name: string;
  
  // CRUD
  add(entry: Omit<MemoryEntry, 'id' | 'createdAt' | 'updatedAt'>): Promise<MemoryEntry>;
  get(id: string): Promise<MemoryEntry | null>;
  update(id: string, content: string): Promise<MemoryEntry | null>;
  delete(id: string): Promise<boolean>;
  
  // Search
  search(query: MemoryQuery): Promise<MemoryResult>;
  list(options?: { source?: string; tags?: string[]; limit?: number }): Promise<MemoryEntry[]>;
  
  // Management
  clear(source?: string): Promise<number>;
  count(): Promise<{ total: number; bySource: Record<string, number> }>;
}

// Provider-specific adapters
export { MarkdownMemoryAdapter } from './markdown';
export { QdrantMemoryAdapter } from './qdrant';
export { MemOSAdapter } from './memos';
export { OpenClawMemoryAdapter } from './openclaw';
