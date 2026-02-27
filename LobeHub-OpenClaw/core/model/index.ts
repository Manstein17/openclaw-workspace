/**
 * Unified Model Interface - 统一模型接口
 *
 * 提供统一的模型调用抽象，屏蔽 LobeHub 和 OpenClaw 的差异
 */

export interface ModelConfig {
  provider: 'openai' | 'anthropic' | 'google' | 'ollama' | 'lobehub' | 'openclaw';
  model: string;
  apiKey?: string;
  baseUrl?: string;
  options?: {
    temperature?: number;
    maxTokens?: number;
    stream?: boolean;
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  images?: string[];
  metadata?: Record<string, any>;
}

export interface ChatResponse {
  content: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  model: string;
}

export interface ModelAdapter {
  name: string;
  config: ModelConfig;
  
  chat(messages: ChatMessage[]): Promise<ChatResponse>;
  stream(messages: ChatMessage[]): AsyncIterable<ChatResponse>;
  getModels(): Promise<string[]>;
  healthCheck(): Promise<boolean>;
}

// Provider-specific adapters
export { OpenAIAdapter } from './openai';
export { AnthropicAdapter } from './anthropic';
export { LobeHubAdapter } from './lobehub';
export { OpenClawAdapter } from './openclaw';
