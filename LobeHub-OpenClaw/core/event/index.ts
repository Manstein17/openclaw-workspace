/**
 * Event Bus - 事件总线
 *
 * 提供跨平台事件触发与响应机制
 */

export interface Event {
  id: string;
  type: string;
  source: 'lobehub' | 'openclaw' | 'user' | 'system';
  payload: Record<string, any>;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface EventHandler {
  (event: Event): Promise<void> | void;
}

export interface EventBusConfig {
  maxQueueSize?: number;
  retryAttempts?: number;
  retryDelay?: number;
}

export class EventBus {
  private handlers: Map<string, EventHandler[]> = new Map();
  private queue: Event[] = [];
  private config: EventBusConfig;

  constructor(config: EventBusConfig = {}) {
    this.config = {
      maxQueueSize: 1000,
      retryAttempts: 3,
      retryDelay: 1000,
      ...config
    };
  }

  /**
   * 订阅事件
   */
  subscribe(eventType: string, handler: EventHandler): () => void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.push(handler);
    this.handlers.set(eventType, handlers);

    // 返回取消订阅函数
    return () => {
      const hs = this.handlers.get(eventType);
      if (hs) {
        const idx = hs.indexOf(handler);
        if (idx !== -1) hs.splice(idx, 1);
      }
    };
  }

  /**
   * 发布事件
   */
  async publish(event: Omit<Event, 'id' | 'timestamp'>): Promise<string> {
    const fullEvent: Event = {
      ...event,
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString()
    };

    // 如果有同步处理器，直接调用
    const handlers = this.handlers.get(event.type) || [];
    const asyncHandlers = handlers.map(h => this.safeExecute(h, fullEvent));

    await Promise.allSettled(asyncHandlers);

    // 加入队列
    this.queue.push(fullEvent);
    if (this.queue.length > this.config.maxQueueSize) {
      this.queue.shift();
    }

    return fullEvent.id;
  }

  /**
   * 安全执行处理器
   */
  private async safeExecute(handler: EventHandler, event: Event): Promise<void> {
    try {
      await handler(event);
    } catch (error) {
      console.error(`Event handler error for ${event.type}:`, error);
    }
  }

  /**
   * 获取事件历史
   */
  getHistory(eventType?: string): Event[] {
    if (eventType) {
      return this.queue.filter(e => e.type === eventType);
    }
    return [...this.queue];
  }

  /**
   * 清空队列
   */
  clear(): void {
    this.queue = [];
  }

  /**
   * 获取统计信息
   */
  getStats(): { queued: number; handlers: Map<string, number> } {
    const handlerCounts = new Map<string, number>();
    this.handlers.forEach((handlers, type) => {
      handlerCounts.set(type, handlers.length);
    });

    return {
      queued: this.queue.length,
      handlers: handlerCounts
    };
  }
}

// 预定义事件类型
export const Events = {
  // LobeHub 事件
  LobeHub: {
    CHAT_COMPLETE: 'lobehub:chat.complete',
    AGENT_CREATED: 'lobehub:agent.created',
    PROMPT_EXPORTED: 'lobehub:prompt.exported',
  },
  
  // OpenClaw 事件
  OpenClaw: {
    TASK_COMPLETE: 'openclaw:task.complete',
    MEMORY_UPDATED: 'openclaw:memory.updated',
    CRON_TRIGGERED: 'openclaw:cron.triggered',
  },
  
  // 通用事件
  Common: {
    MEMORY_SHARED: 'memory:shared',
    SKILL_INVOKED: 'skill:invoked',
    ERROR: 'error',
  }
} as const;
