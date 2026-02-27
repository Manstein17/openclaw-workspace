/**
 * OpenClaw Adapter - OpenClaw Gateway API 适配器
 *
 * 提供 OpenClaw Gateway RPC 完整实现
 */

import { ModelAdapter, ModelConfig, ChatMessage, ChatResponse } from './index';

export class OpenClawModelAdapter implements ModelAdapter {
  name = 'openclaw';
  private config: ModelConfig;
  private gatewayUrl: string;
  private apiKey: string;

  constructor(config: ModelConfig) {
    this.config = config;
    this.gatewayUrl = config.baseUrl || process.env.OPENCLAW_GATEWAY_URL || 'http://localhost:18789';
    this.apiKey = config.apiKey || '';
  }

  /**
   * 通过 Gateway RPC 调用模型
   */
  async chat(messages: ChatMessage[]): Promise<ChatResponse> {
    const session = await this.createSession();
    
    const systemMsg = messages.find(m => m.role === 'system');
    const userMsgs = messages.filter(m => m.role !== 'system');

    // 构建会话消息
    const body = {
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method: 'session.send',
      params: {
        sessionId: session.id,
        message: {
          role: 'user',
          content: userMsgs[userMsgs.length - 1]?.content || '',
        },
      },
    };

    // 如果有 system prompt，使用 session.edit
    if (systemMsg) {
      await fetch(`${this.gatewayUrl}/api/session/${session.id}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          systemMessage: systemMsg.content,
        }),
      });
    }

    const response = await fetch(`${this.gatewayUrl}/api/session/${session.id}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body.params),
    });

    if (!response.ok) {
      throw new Error(`OpenClaw API error: ${response.statusText}`);
    }

    const data = await response.json();
    
    // 获取使用统计
    const stats = await this.getSessionStats(session.id);

    return {
      content: data.result?.content || data.content || '',
      usage: stats,
      model: this.config.model || 'claude-opus-4',
    };
  }

  async *stream(messages: ChatMessage[]): AsyncIterable<ChatResponse> {
    // OpenClaw Gateway 支持流式响应
    const session = await this.createSession();
    let content = '';

    const systemMsg = messages.find(m => m.role === 'system');
    const userMsgs = messages.filter(m => m.role !== 'system');

    // 设置 system message
    if (systemMsg) {
      await fetch(`${this.gatewayUrl}/api/session/${session.id}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ systemMessage: systemMsg.content }),
      });
    }

    // 发送用户消息并获取流
    const response = await fetch(`${this.gatewayUrl}/api/session/${session.id}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: session.id,
        message: {
          role: 'user',
          content: userMsgs[userMsgs.length - 1]?.content || '',
        },
        stream: true,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`OpenClaw stream error: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      content += chunk;

      yield {
        content,
        usage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
        model: this.config.model || 'claude-opus-4',
      };
    }
  }

  async getModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.gatewayUrl}/api/models`);
      if (!response.ok) return ['claude-opus-4', 'claude-sonnet-4'];
      const data = await response.json();
      return data.models || [];
    } catch {
      return ['claude-opus-4', 'claude-sonnet-4', 'gpt-4'];
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.gatewayUrl}/api/status`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * 创建会话
   */
  private async createSession(): Promise<{ id: string; model: string }> {
    const response = await fetch(`${this.gatewayUrl}/api/session/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.config.model || 'claude-opus-4',
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 获取会话统计
   */
  private async getSessionStats(sessionId: string): Promise<{
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  }> {
    try {
      const response = await fetch(`${this.gatewayUrl}/api/session/${sessionId}/stats`);
      if (!response.ok) return { promptTokens: 0, completionTokens: 0, totalTokens: 0 };
      return response.json();
    } catch {
      return { promptTokens: 0, completionTokens: 0, totalTokens: 0 };
    }
  }
}

/**
 * OpenClaw Gateway RPC Client
 */
export class OpenClawGateway {
  private baseUrl: string;

  constructor(gatewayUrl?: string) {
    this.baseUrl = gatewayUrl || process.env.OPENCLAW_GATEWAY_URL || 'http://localhost:18789';
  }

  async createSession(model?: string): Promise<{ id: string; model: string }> {
    const response = await fetch(`${this.baseUrl}/api/session/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model }),
    });
    return response.json();
  }

  async sendMessage(sessionId: string, message: { role: string; content: string }): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/session/${sessionId}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId, message }),
    });
    return response.json();
  }

  async editSession(sessionId: string, systemMessage?: string): Promise<void> {
    await fetch(`${this.baseUrl}/api/session/${sessionId}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ systemMessage }),
    });
  }

  async getSessionHistory(sessionId: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/session/${sessionId}/history`);
    return response.json();
  }

  async deleteSession(sessionId: string): Promise<void> {
    await fetch(`${this.baseUrl}/api/session/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async listSessions(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/sessions`);
    return response.json();
  }

  async getGatewayStatus(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/status`);
    return response.json();
  }
}
