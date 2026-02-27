/**
 * LobeHub Adapter - LobeHub API 适配器
 *
 * LobeHub (LobeChat) 使用 OpenAI 兼容 API
 * 文档: https://lobehub.com/docs/development/basic/chat-api
 */

import { ModelAdapter, ModelConfig, ChatMessage, ChatResponse } from './index';

export interface LobeHubConfig {
  baseUrl?: string;      // LobeHub 服务地址，默认 http://localhost:3210
  apiKey?: string;       // API Key（如果需要）
}

export class LobeHubAdapter implements ModelAdapter {
  name = 'lobehub';
  private config: LobeHubConfig;
  private baseUrl: string;
  private apiKey: string;

  constructor(config: LobeHubConfig = {}) {
    this.config = config;
    this.baseUrl = config.baseUrl || process.env.LOBEHUB_URL || 'http://localhost:3210';
    this.apiKey = config.apiKey || '';
  }

  /**
   * 发送聊天消息
   */
  async chat(messages: ChatMessage[]): Promise<ChatResponse> {
    // LobeHub 使用 OpenAI 兼容格式
    const url = `${this.baseUrl}/api/chat`;

    const systemMsg = messages.find(m => m.role === 'system');
    const userMsgs = messages.filter(m => m.role !== 'system');

    const body = {
      messages: userMsgs.map(m => ({
        role: m.role,
        content: m.content,
      })),
      model: this.config.model || 'gpt-4',
      temperature: this.config.options?.temperature || 0.7,
      max_tokens: this.config.options?.maxTokens || 4096,
      stream: false,
    };

    // 如果有 system message，需要特殊处理
    // LobeHub 可能通过 config 或第一条 message 传递
    if (systemMsg) {
      (body as any).system_prompt = systemMsg.content;
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`LobeHub API error: ${error}`);
    }

    const data = await response.json();

    return {
      content: data.choices?.[0]?.message?.content || data.content || '',
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
      model: data.model || this.config.model || 'gpt-4',
    };
  }

  /**
   * 流式聊天
   */
  async *stream(messages: ChatMessage[]): AsyncIterable<ChatResponse> {
    const url = `${this.baseUrl}/api/chat/stream`;

    const systemMsg = messages.find(m => m.role === 'system');
    const userMsgs = messages.filter(m => m.role !== 'system');

    const body = {
      messages: userMsgs.map(m => ({
        role: m.role,
        content: m.content,
      })),
      model: this.config.model || 'gpt-4',
      temperature: this.config.options?.temperature || 0.7,
      max_tokens: this.config.options?.maxTokens || 4096,
      stream: true,
    };

    if (systemMsg) {
      (body as any).system_prompt = systemMsg.content;
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok || !response.body) {
      throw new Error(`LobeHub stream error: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let content = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(l => l.trim() && !l.startsWith('data: '));

      for (const line of lines) {
        try {
          // LobeHub SSE 格式
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            // 处理不同类型的消息
            if (data.type === 'content' || data.delta?.content) {
              content += data.delta?.content || data.content || '';
              yield {
                content,
                usage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
                model: this.config.model || 'gpt-4',
              };
            } else if (data.type === 'finish' || data.type === 'stop') {
              // 流结束，yield 最终内容
              yield {
                content,
                usage: data.usage || { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
                model: this.config.model || 'gpt-4',
              };
              return;
            }
          }
        } catch {
          // 忽略解析错误
        }
      }

      // 处理原始 SSE
      if (chunk.includes('[DONE]')) {
        return;
      }
    }
  }

  /**
   * 获取可用模型列表
   */
  async getModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/models`, {
        headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
      });

      if (!response.ok) {
        // LobeHub 可能使用不同端点
        return this.getDefaultModels();
      }

      const data = await response.json();
      return data.models || data.data?.map((m: any) => m.id) || [];
    } catch {
      return this.getDefaultModels();
    }
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`, {
        headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
      });

      // LobeHub 可能返回不同格式
      if (response.ok) return true;

      // 尝试检查 WebSocket 连接
      const wsResponse = await fetch(`${this.baseUrl.replace('http', 'ws')}/ws`, {
        method: 'GET',
      });

      return wsResponse.ok || false;
    } catch {
      return false;
    }
  }

  /**
   * 创建助手
   */
  async createAssistant(options: {
    name: string;
    systemPrompt: string;
    model: string;
    avatar?: string;
    tags?: string[];
  }): Promise<string> {
    const url = `${this.baseUrl}/api/assistant`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
      },
      body: JSON.stringify(options),
    });

    if (!response.ok) {
      throw new Error(`Failed to create assistant: ${response.statusText}`);
    }

    const data = await response.json();
    return data.id || data.assistant_id;
  }

  /**
   * 导出助手
   */
  async exportAssistant(assistantId: string): Promise<any> {
    const url = `${this.baseUrl}/api/assistant/${assistantId}/export`;

    const response = await fetch(url, {
      headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
    });

    if (!response.ok) {
      throw new Error(`Failed to export assistant: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 获取会话历史
   */
  async getSessionHistory(sessionId: string): Promise<any[]> {
    const url = `${this.baseUrl}/api/chat/${sessionId}`;

    const response = await fetch(url, {
      headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
    });

    if (!response.ok) return [];

    return response.json();
  }

  /**
   * 获取助手市场列表
   */
  async listAssistants(): Promise<Array<{ id: string; name: string; description: string }>> {
    try {
      const url = `${this.baseUrl}/api/assistants`;

      const response = await fetch(url, {
        headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
      });

      if (!response.ok) return [];

      const data = await response.json();
      return data.assistants || data.data || [];
    } catch {
      return [];
    }
  }

  /**
   * 默认模型列表
   */
  private getDefaultModels(): string[] {
    return [
      'gpt-4',
      'gpt-4-turbo',
      'gpt-3.5-turbo',
      'claude-3-opus',
      'claude-3-sonnet',
      'claude-3-haiku',
      'gemini-pro',
      'local-llama',
    ];
  }
}

/**
 * LobeHub WebSocket 连接
 */
export class LobeHubWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, Function[]> = new Map();

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        resolve();
      };

      this.ws.onerror = (error) => {
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const handlers = this.handlers.get(data.type) || [];
          handlers.forEach(h => h(data));
        } catch {
          // 忽略解析错误
        }
      };
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(type: string, payload: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  on(type: string, handler: Function): void {
    const handlers = this.handlers.get(type) || [];
    handlers.push(handler);
    this.handlers.set(type, handlers);
  }

  off(type: string, handler: Function): void {
    const handlers = this.handlers.get(type) || [];
    const idx = handlers.indexOf(handler);
    if (idx !== -1) handlers.splice(idx, 1);
  }
}
