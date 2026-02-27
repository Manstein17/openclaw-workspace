/**
 * Cross-Platform Trigger Integration - 跨平台触发模块
 *
 * 实现 LobeHub 与 OpenClaw 之间的事件触发与响应
 */

import { EventBus, Event, Events } from '../core/event';
import { OpenClawPlatformAdapter } from '../adapters/openclaw';
import { LobeHubPlatformAdapter } from '../adapters/lobehub';

export interface CrossTriggerConfig {
  lobehubWsUrl?: string;        // LobeHub WebSocket URL
  openclawGatewayUrl?: string;   // OpenClaw Gateway URL
  webhookSecret?: string;        // Webhook 密钥
  autoConnect?: boolean;
}

export interface TriggerRule {
  id: string;
  name: string;
  enabled: boolean;
  condition: {
    platform: 'lobehub' | 'openclaw';
    event: string;
    filter?: Record<string, any>;
  };
  action: {
    platform: 'lobehub' | 'openclaw';
    type: string;
    params: Record<string, any>;
  };
}

export class CrossTriggerIntegration {
  private config: CrossTriggerConfig;
  private eventBus: EventBus;
  private openclaw: OpenClawPlatformAdapter;
  private lobehub: LobeHubPlatformAdapter;
  
  private wsOpenclaw: WebSocket | null = null;
  private wsLobehub: WebSocket | null = null;
  private rules: Map<string, TriggerRule> = new Map();
  private unsubscribe: (() => void)[] = [];

  constructor(
    config: CrossTriggerConfig,
    eventBus: EventBus,
    openclaw: OpenClawPlatformAdapter,
    lobehub: LobeHubPlatformAdapter
  ) {
    this.config = {
      autoConnect: true,
      lobehubWsUrl: process.env.LOBEHUB_WS_URL || 'ws://localhost:3210/ws',
      openclawGatewayUrl: process.env.OPENCLAW_GATEWAY_URL || 'ws://localhost:18789/ws',
      ...config,
    };
    this.eventBus = eventBus;
    this.openclaw = openclaw;
    this.lobehub = lobehub;
  }

  /**
   * 初始化并连接
   */
  async init(): Promise<void> {
    // 设置默认触发规则
    this.setupDefaultRules();

    // 监听跨平台事件
    this.setupEventListeners();

    if (this.config.autoConnect) {
      await this.connect();
    }
  }

  /**
   * 连接到两个平台
   */
  async connect(): Promise<void> {
    await Promise.all([
      this.connectOpenClaw(),
      this.connectLobeHub(),
    ]);

    console.log('Cross-trigger connected to both platforms');
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.wsOpenclaw) {
      this.wsOpenclaw.close();
      this.wsOpenclaw = null;
    }
    if (this.wsLobehub) {
      this.wsLobehub.close();
      this.wsLobehub = null;
    }

    this.unsubscribe.forEach(u => u());
    this.unsubscribe = [];
  }

  /**
   * 连接 OpenClaw Gateway
   */
  private async connectOpenClaw(): Promise<void> {
    try {
      // OpenClaw Gateway HTTP API 已足够
      // 如果需要实时事件，可以通过轮询或 WebSocket
      console.log('OpenClaw connected via HTTP API');
    } catch (error) {
      console.error('Failed to connect OpenClaw:', error);
    }
  }

  /**
   * 连接 LobeHub WebSocket
   */
  private async connectLobeHub(): Promise<void> {
    try {
      // LobeHub 支持 WebSocket 连接
      this.wsLobehub = new WebSocket(this.config.lobehubWsUrl!);

      this.wsLobehub.onopen = () => {
        console.log('Connected to LobeHub WebSocket');
      };

      this.wsLobehub.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          await this.handleLobeHubMessage(data);
        } catch (error) {
          // 忽略解析错误
        }
      };

      this.wsLobehub.onerror = (error) => {
        console.error('LobeHub WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect LobeHub:', error);
    }
  }

  /**
   * 处理 LobeHub 消息
   */
  private async handleLobeHubMessage(data: any): Promise<void> {
    // 发布事件到总线
    await this.eventBus.publish({
      type: `lobehub:${data.type}`,
      source: 'cross-trigger',
      payload: data,
    });

    // 检查触发规则
    await this.checkRules('lobehub', data.type, data);
  }

  /**
   * 从 LobeHub 触发 OpenClaw 任务
   */
  async triggerOpenClawFromLobeHub(options: {
    prompt: string;
    session?: string;
    channel?: string;
  }): Promise<string> {
    const eventId = crypto.randomUUID();

    // 发布事件
    await this.eventBus.publish({
      type: 'cross:lobehub->openclaw',
      source: 'cross-trigger',
      payload: {
        id: eventId,
        prompt: options.prompt,
        session: options.session,
        channel: options.channel,
        timestamp: new Date().toISOString(),
      },
    });

    // 执行 OpenClaw 会话
    try {
      await this.openclaw.chat({
        messages: [{ role: 'user', content: options.prompt }],
        session: options.session,
      });
    } catch (error) {
      console.error('Trigger OpenClaw failed:', error);
    }

    return eventId;
  }

  /**
   * 从 OpenClaw 触发 LobeHub 对话
   */
  async triggerLobeHubFromOpenClaw(options: {
    prompt: string;
    agentId?: string;
    stream?: boolean;
  }): Promise<string> {
    const eventId = crypto.randomUUID();

    await this.eventBus.publish({
      type: 'cross:openclaw->lobehub',
      source: 'cross-trigger',
      payload: {
        id: eventId,
        prompt: options.prompt,
        agentId: options.agentId,
        stream: options.stream,
        timestamp: new Date().toISOString(),
      },
    });

    try {
      await this.lobehub.chat({
        messages: [{ role: 'user', content: options.prompt }],
        agentId: options.agentId,
        stream: options.stream,
      });
    } catch (error) {
      console.error('Trigger LobeHub failed:', error);
    }

    return eventId;
  }

  /**
   * 添加触发规则
   */
  addRule(rule: Omit<TriggerRule, 'id'>): string {
    const id = crypto.randomUUID();
    this.rules.set(id, { ...rule, id });
    return id;
  }

  /**
   * 移除触发规则
   */
  removeRule(id: string): boolean {
    return this.rules.delete(id);
  }

  /**
   * 获取所有规则
   */
  getRules(): TriggerRule[] {
    return Array.from(this.rules.values());
  }

  /**
   * 启用/禁用规则
   */
  setRuleEnabled(id: string, enabled: boolean): boolean {
    const rule = this.rules.get(id);
    if (rule) {
      rule.enabled = enabled;
      return true;
    }
    return false;
  }

  /**
   * 设置默认触发规则
   */
  private setupDefaultRules(): void {
    // LobeHub 对话完成 → 同步到 OpenClaw
    this.addRule({
      name: 'LobeHub Chat → OpenClaw',
      enabled: true,
      condition: {
        platform: 'lobehub',
        event: 'chat.complete',
      },
      action: {
        platform: 'openclaw',
        type: 'log_memory',
        params: {},
      },
    });

    // OpenClaw 任务完成 → 同步到 LobeHub
    this.addRule({
      name: 'OpenClaw Task → LobeHub',
      enabled: true,
      condition: {
        platform: 'openclaw',
        event: 'task.complete',
      },
      action: {
        platform: 'lobehub',
        type: 'notify',
        params: {},
      },
    });

    // 记忆更新 → 两边同步
    this.addRule({
      name: 'Memory Update → Cross Sync',
      enabled: true,
      condition: {
        platform: 'openclaw',
        event: 'memory.updated',
      },
      action: {
        platform: 'lobehub',
        type: 'refresh_memory',
        params: {},
      },
    });
  }

  /**
   * 设置事件监听
   */
  private setupEventListeners(): void {
    // 监听所有事件
    const unsub = this.eventBus.subscribe('*', async (event: Event) => {
      await this.checkRules(event.source, event.type, event.payload);
    });
    this.unsubscribe.push(unsub);
  }

  /**
   * 检查触发规则
   */
  private async checkRules(
    platform: string,
    eventType: string,
    payload: any
  ): Promise<void> {
    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue;
      if (rule.condition.platform !== platform) continue;
      if (rule.condition.event !== eventType) continue;

      // 检查过滤条件
      if (rule.condition.filter) {
        const matches = Object.entries(rule.condition.filter).every(
          ([key, value]) => payload[key] === value
        );
        if (!matches) continue;
      }

      // 执行动作
      await this.executeAction(rule.action, payload);
    }
  }

  /**
   * 执行动作
   */
  private async executeAction(
    action: TriggerRule['action'],
    context: any
  ): Promise<void> {
    switch (action.type) {
      case 'log_memory':
        // 记录到记忆
        await this.logToMemory(action.platform, context);
        break;

      case 'notify':
        // 发送通知
        await this.sendNotification(action.platform, context);
        break;

      case 'refresh_memory':
        // 刷新记忆
        await this.refreshMemory(action.platform);
        break;

      case 'execute_skill':
        // 执行 Skill
        if (action.params.skillId) {
          await this.executeSkill(action.params.skillId, context);
        }
        break;

      default:
        console.log(`Unknown action type: ${action.type}`);
    }
  }

  /**
   * 记录到记忆
   */
  private async logToMemory(platform: string, context: any): Promise<void> {
    await this.eventBus.publish({
      type: 'memory:cross_platform_log',
      source: 'cross-trigger',
      payload: {
        from: platform,
        content: context,
        timestamp: new Date().toISOString(),
      },
    });
  }

  /**
   * 发送通知
   */
  private async sendNotification(platform: string, context: any): Promise<void> {
    await this.eventBus.publish({
      type: 'notification:cross_platform',
      source: 'cross-trigger',
      payload: {
        from: platform,
        message: context.message || 'Cross-platform event',
      },
    });
  }

  /**
   * 刷新记忆
   */
  private async refreshMemory(platform: string): Promise<void> {
    await this.eventBus.publish({
      type: 'memory:refresh_request',
      source: 'cross-trigger',
      payload: { from: platform },
    });
  }

  /**
   * 执行 Skill
   */
  private async executeSkill(skillId: string, context: any): Promise<void> {
    await this.eventBus.publish({
      type: 'skill:execute_request',
      source: 'cross-trigger',
      payload: { skillId, context },
    });
  }

  /**
   * 获取连接状态
   */
  getStatus(): {
    connected: boolean;
    rules: number;
    enabledRules: number;
    wsLobehub: boolean;
    wsOpenclaw: boolean;
  } {
    const rules = this.getRules();
    return {
      connected: !!(this.wsLobehub || this.wsOpenclaw),
      rules: rules.length,
      enabledRules: rules.filter(r => r.enabled).length,
      wsLobehub: this.wsLobehub?.readyState === WebSocket.OPEN,
      wsOpenclaw: false, // OpenClaw 使用 HTTP
    };
  }
}

/**
 * WebSocket 工具类
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, Function[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
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
          // 忽略
        }
      };

      this.ws.onclose = () => {
        this.attemptReconnect();
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

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect().catch(() => {});
    }, delay);
  }
}
