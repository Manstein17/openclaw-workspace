/**
 * OpenAI Adapter - OpenAI 模型适配器
 *
 * 提供 OpenAI API 完整实现
 */

import { ModelAdapter, ModelConfig, ChatMessage, ChatResponse } from './index';

export class OpenAIAdapter implements ModelAdapter {
  name = 'openai';
  private config: ModelConfig;
  private baseUrl: string;
  private apiKey: string;

  constructor(config: ModelConfig) {
    this.config = config;
    this.baseUrl = config.baseUrl || 'https://api.openai.com/v1';
    this.apiKey = config.apiKey || process.env.OPENAI_API_KEY || '';
  }

  async chat(messages: ChatMessage[]): Promise<ChatResponse> {
    const url = `${this.baseUrl}/chat/completions`;
    
    const body = {
      model: this.config.model || 'gpt-4',
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
        ...(m.images && { content: [
          ...m.images.map(img => ({ type: 'image_url', image_url: { url: img } })),
          { type: 'text', text: m.content }
        ]})
      })),
      temperature: this.config.options?.temperature || 0.7,
      max_tokens: this.config.options?.maxTokens || 4096,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`OpenAI API error: ${error}`);
    }

    const data = await response.json();
    
    return {
      content: data.choices[0].message.content,
      usage: {
        promptTokens: data.usage.prompt_tokens,
        completionTokens: data.usage.completion_tokens,
        totalTokens: data.usage.total_tokens,
      },
      model: this.config.model || 'gpt-4',
    };
  }

  async *stream(messages: ChatMessage[]): AsyncIterable<ChatResponse> {
    const url = `${this.baseUrl}/chat/completions`;
    
    const body = {
      model: this.config.model || 'gpt-4',
      messages: messages.map(m => ({ role: m.role, content: m.content })),
      temperature: this.config.options?.temperature || 0.7,
      max_tokens: this.config.options?.maxTokens || 4096,
      stream: true,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let content = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(l => l.trim().startsWith('data: '));

      for (const line of lines) {
        const data = line.replace('data: ', '');
        if (data === '[DONE]') return;
        
        try {
          const parsed = JSON.parse(data);
          const delta = parsed.choices[0]?.delta?.content;
          if (delta) {
            content += delta;
            yield {
              content: content,
              usage: {
                promptTokens: 0,
                completionTokens: 0,
                totalTokens: 0,
              },
              model: this.config.model || 'gpt-4',
            };
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
  }

  async getModels(): Promise<string[]> {
    if (!this.apiKey) {
      return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'];
    }

    try {
      const response = await fetch(`${this.baseUrl}/models`, {
        headers: { 'Authorization': `Bearer ${this.apiKey}` },
      });
      const data = await response.json();
      return data.data
        ?.filter((m: any) => m.id.startsWith('gpt'))
        ?.map((m: any) => m.id) || [];
    } catch {
      return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'];
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/models`, {
        headers: { 'Authorization': `Bearer ${this.apiKey}` },
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
