/**
 * Anthropic Adapter - Anthropic Claude 模型适配器
 *
 * 提供 Anthropic API 完整实现
 */

import { ModelAdapter, ModelConfig, ChatMessage, ChatResponse } from './index';

export class AnthropicAdapter implements ModelAdapter {
  name = 'anthropic';
  private config: ModelConfig;
  private baseUrl: string;
  private apiKey: string;

  constructor(config: ModelConfig) {
    this.config = config;
    this.baseUrl = 'https://api.anthropic.com/v1';
    this.apiKey = config.apiKey || process.env.ANTHROPIC_API_KEY || '';
  }

  async chat(messages: ChatMessage[]): Promise<ChatResponse> {
    const url = `${this.baseUrl}/messages`;
    
    // 转换消息格式
    const systemMsg = messages.find(m => m.role === 'system');
    const userMsgs = messages.filter(m => m.role !== 'system');

    const body = {
      model: this.config.model || 'claude-sonnet-4-20250514',
      max_tokens: this.config.options?.maxTokens || 4096,
      temperature: this.config.options?.temperature || 0.7,
      system: systemMsg?.content,
      messages: userMsgs.map(m => ({
        role: m.role,
        content: m.content,
      })),
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Anthropic API error: ${error}`);
    }

    const data = await response.json();
    
    return {
      content: data.content[0].text,
      usage: {
        promptTokens: data.usage.input_tokens,
        completionTokens: data.usage.output_tokens,
        totalTokens: data.usage.input_tokens + data.usage.output_tokens,
      },
      model: this.config.model || 'claude-sonnet-4-20250514',
    };
  }

  async *stream(messages: ChatMessage[]): AsyncIterable<ChatResponse> {
    const url = `${this.baseUrl}/messages`;
    
    const systemMsg = messages.find(m => m.role === 'system');
    const userMsgs = messages.filter(m => m.role !== 'system');

    const body = {
      model: this.config.model || 'claude-sonnet-4-20250514',
      max_tokens: this.config.options?.maxTokens || 4096,
      temperature: this.config.options?.temperature || 0.7,
      system: systemMsg?.content,
      messages: userMsgs.map(m => ({
        role: m.role,
        content: m.content,
      })),
      stream: true,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Anthropic API error: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let content = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(l => l.trim() && l.trim() !== 'event: ping');

      for (const line of lines) {
        if (line.startsWith('event: ')) continue;
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'content_block_delta') {
              const delta = data.delta?.text;
              if (delta) {
                content += delta;
                yield {
                  content: content,
                  usage: {
                    promptTokens: 0,
                    completionTokens: 0,
                    totalTokens: 0,
                  },
                  model: this.config.model || 'claude-sonnet-4-20250514',
                };
              }
            } else if (data.type === 'message_stop') {
              return;
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    }
  }

  async getModels(): Promise<string[]> {
    return [
      'claude-opus-4-20250514',
      'claude-sonnet-4-20250514',
      'claude-haiku-3-20250520',
    ];
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: 'claude-haiku-3-20250520',
          max_tokens: 1,
          messages: [{ role: 'user', content: 'hi' }],
        }),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
