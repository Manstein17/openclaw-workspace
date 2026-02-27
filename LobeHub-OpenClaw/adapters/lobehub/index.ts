/**
 * LobeHub Platform Adapter - LobeHub 平台适配器
 *
 * 对接 LobeHub (LobeChat) 官方服务
 */

import { LobeHubAdapter, LobeHubWebSocket } from '../core/model/lobehub';
import { EventBus, Events } from '../core/event';

export interface LobeHubPlatformConfig {
  baseUrl?: string;
  apiKey?: string;
  workspaceDir?: string;
}

export class LobeHubPlatformAdapter {
  name = 'lobehub';
  
  private config: LobeHubPlatformConfig;
  private eventBus: EventBus;
  private modelAdapter: LobeHubAdapter;
  private ws: LobeHubWebSocket | null = null;
  private connected: boolean = false;

  constructor(config: LobeHubPlatformConfig = {}, eventBus: EventBus) {
    this.config = {
      baseUrl: process.env.LOBEHUB_URL || 'http://localhost:3210',
      ...config,
    };
    this.eventBus = eventBus;
    this.modelAdapter = new LobeHubAdapter(this.config);
  }

  /**
   * 连接到 LobeHub
   */
  async connect(): Promise<void> {
    try {
      // 检查健康状态
      const healthy = await this.modelAdapter.healthCheck();
      
      if (!healthy) {
        // 尝试 WebSocket 连接
        try {
          this.ws = new LobeHubWebSocket(this.config.baseUrl?.replace('http', 'ws') + '/ws');
          await this.ws.connect();
          this.setupWebSocketHandlers();
        } catch {
          throw new Error(`Cannot connect to LobeHub at ${this.config.baseUrl}`);
        }
      }

      this.connected = true;
      
      // 发布连接成功事件
      await this.eventBus.publish({
        type: Events.LobeHub.AGENT_CREATED,
        source: 'lobehub-adapter',
        payload: { connected: true },
      });
    } catch (error) {
      console.error('LobeHub connection error:', error);
      throw error;
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.disconnect();
      this.ws = null;
    }
    this.connected = false;
  }

  /**
   * 发送聊天消息
   */
  async chat(options: {
    messages: Array<{ role: string; content: string }>;
    agentId?: string;
    stream?: boolean;
  }): Promise<string> {
    const messages = options.messages.map(m => ({
      role: m.role as 'user' | 'assistant' | 'system',
      content: m.content,
    }));

    if (options.stream) {
      const generator = this.modelAdapter.stream(messages);
      let result = '';
      
      for await (const response of generator) {
        result = response.content;
        // 可以在此 yield 中间结果
      }

      // 发布聊天完成事件
      await this.eventBus.publish({
        type: Events.LobeHub.CHAT_COMPLETE,
        source: 'lobehub-adapter',
        payload: { content: result },
      });

      return result;
    }

    const response = await this.modelAdapter.chat(messages);
    
    await this.eventBus.publish({
      type: Events.LobeHub.CHAT_COMPLETE,
      source: 'lobehub-adapter',
      payload: { content: response.content },
    });

    return response.content;
  }

  /**
   * 创建助手
   */
  async createAssistant(assistant: {
    name: string;
    systemPrompt: string;
    model: string;
    avatar?: string;
    tags?: string[];
  }): Promise<string> {
    const id = await this.modelAdapter.createAssistant(assistant);

    await this.eventBus.publish({
      type: Events.LobeHub.AGENT_CREATED,
      source: 'lobehub-adapter',
      payload: { id, name: assistant.name },
    });

    return id;
  }

  /**
   * 导出助手配置
   */
  async exportAssistant(assistantId: string): Promise<any> {
    const assistant = await this.modelAdapter.exportAssistant(assistantId);

    await this.eventBus.publish({
      type: Events.LobeHub.PROMPT_EXPORTED,
      source: 'lobehub-adapter',
      payload: { assistantId },
    });

    return assistant;
  }

  /**
   * 获取可用模型列表
   */
  async getModels(): Promise<string[]> {
    return this.modelAdapter.getModels();
  }

  /**
   * 获取助手列表
   */
  async listAssistants(): Promise<Array<{ id: string; name: string; description: string }>> {
    return this.modelAdapter.listAssistants();
  }

  /**
   * 获取会话历史
   */
  async getSessionHistory(sessionId: string): Promise<any[]> {
    return this.modelAdapter.getSessionHistory(sessionId);
  }

  /**
   * 导出对话到 OpenClaw 格式
   */
  async exportConversationToOpenClaw(sessionId: string): Promise<string> {
    const history = await this.getSessionHistory(sessionId);
    
    // 转换为 Markdown 格式
    let md = `# LobeHub Conversation Export\n\n`;
    md += `Date: ${new Date().toISOString()}\n\n`;
    
    for (const msg of history) {
      const role = msg.role === 'user' ? '## User' : '## Assistant';
      md += `${role}\n\n${msg.content}\n\n`;
    }

    // 发布导出事件
    await this.eventBus.publish({
      type: Events.LobeHub.PROMPT_EXPORTED,
      source: 'lobehub-adapter',
      payload: { sessionId, format: 'markdown' },
    });

    return md;
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.connected;
  }

  /**
   * 设置 WebSocket 处理器
   */
  private setupWebSocketHandlers(): void {
    if (!this.ws) return;

    this.ws.on('message', async (data: any) => {
      // 处理实时消息
      await this.eventBus.publish({
        type: 'lobehub:websocket.message',
        source: 'lobehub-adapter',
        payload: data,
      });
    });

    this.ws.on('error', async (error: any) => {
      await this.eventBus.publish({
        type: 'lobehub:websocket.error',
        source: 'lobehub-adapter',
        payload: { error: error.message },
      });
    });
  }
}

/**
 * LobeHub Agent 导入器
 *
 * 将 LobeHub 助手导入为 Skills
 */
export class LobeHubAgentImporter {
  private adapter: LobeHubPlatformAdapter;

  constructor(adapter: LobeHubPlatformAdapter) {
    this.adapter = adapter;
  }

  /**
   * 导入助手为 Skill
   */
  async importAsSkill(assistantId: string, options?: {
    name?: string;
    tags?: string[];
  }): Promise<{
    id: string;
    name: string;
    prompt: string;
    tags: string[];
  }> {
    const assistant = await this.adapter.exportAssistant(assistantId);

    return {
      id: `lobehub-${assistantId}`,
      name: options?.name || assistant.name || 'Imported Agent',
      prompt: assistant.system_prompt || assistant.systemPrompt || '',
      tags: [...(options?.tags || []), 'lobehub', 'imported'],
    };
  }

  /**
   * 批量导入助手
   */
  async importAll(): Promise<Array<{
    id: string;
    name: string;
    prompt: string;
    tags: string[];
  }>> {
    const assistants = await this.adapter.listAssistants();
    const results = [];

    for (const ass of assistants) {
      try {
        const skill = await this.importAsSkill(ass.id);
        results.push(skill);
      } catch (error) {
        console.error(`Failed to import assistant ${ass.id}:`, error);
      }
    }

    return results;
  }
}
