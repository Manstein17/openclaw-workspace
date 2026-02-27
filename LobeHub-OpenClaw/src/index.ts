/**
 * LobeHub-OpenClaw - 主入口
 *
 * 系统架构级整合入口文件
 */

import { EventBus, Events } from './core/event';
import { ModelAdapter } from './core/model';
import { MemoryAdapter } from './core/memory';
import { SharedMemoryIntegration } from './integrations/shared-memory';
import { SharedSkillsIntegration } from './integrations/shared-skills';
import { CrossTriggerIntegration } from './integrations/cross-trigger';
import { OpenClawPlatformAdapter } from './adapters/openclaw';
import { LobeHubPlatformAdapter } from './adapters/lobehub';

export interface LobeHubOpenClawConfig {
  openclaw?: {
    gatewayUrl: string;
    workspaceDir: string;
  };
  lobehub?: {
    baseUrl: string;
  };
  memory?: {
    type: 'markdown' | 'qdrant' | 'memos';
    dir?: string;
  };
  integrations?: {
    sharedMemory?: boolean;
    sharedSkills?: boolean;
    crossTrigger?: boolean;
  };
}

export class LobeHubOpenClaw {
  // Core
  eventBus: EventBus;
  
  // Adapters
  openclaw: OpenClawPlatformAdapter;
  lobehub: LobeHubPlatformAdapter;
  
  // Integrations
  sharedMemory?: SharedMemoryIntegration;
  sharedSkills?: SharedSkillsIntegration;
  crossTrigger?: CrossTriggerIntegration;

  private constructor(config: LobeHubOpenClawConfig) {
    // 初始化事件总线
    this.eventBus = new EventBus();

    // 初始化平台适配器
    this.openclaw = new OpenClawPlatformAdapter(
      config.openclaw || { gatewayUrl: 'http://localhost:18789', workspaceDir: '.' },
      this.eventBus
    );
    
    this.lobehub = new LobeHubPlatformAdapter(
      config.lobehub || {},
      this.eventBus
    );

    // 初始化整合模块
    if (config.integrations?.sharedMemory) {
      // TODO: 初始化记忆共享
    }

    if (config.integrations?.sharedSkills) {
      // TODO: 初始化 Skills 共享
    }

    if (config.integrations?.crossTrigger) {
      // TODO: 初始化跨平台触发
    }
  }

  /**
   * 创建实例
   */
  static async create(config: LobeHubOpenClawConfig): Promise<LobeHubOpenClaw> {
    const instance = new LobeHubOpenClaw(config);
    
    // 启动时连接各平台
    await instance.connect();
    
    return instance;
  }

  /**
   * 连接所有平台
   */
  async connect(): Promise<void> {
    await Promise.all([
      this.openclaw.connect(),
      this.lobehub.connect()
    ]);
  }

  /**
   * 断开所有连接
   */
  disconnect(): void {
    this.openclaw.disconnect();
    this.lobehub.disconnect();
    this.sharedMemory?.stop();
  }

  /**
   * 获取系统状态
   */
  async status(): Promise<{
    openclaw: boolean;
    lobehub: boolean;
    integrations: Record<string, boolean>;
  }> {
    return {
      openclaw: this.openclaw.isConnected(),
      lobehub: this.lobehub.isConnected(),
      integrations: {
        sharedMemory: !!this.sharedMemory,
        sharedSkills: !!this.sharedSkills,
        crossTrigger: !!this.crossTrigger
      }
    };
  }
}

// 导出所有模块
export { EventBus, Events } from './core/event';
export { ModelAdapter } from './core/model';
export { MemoryAdapter } from './core/memory';
export { Skill, SkillManifest } from './core/skill';
export { SharedMemoryIntegration } from './integrations/shared-memory';
export { SharedSkillsIntegration } from './integrations/shared-skills';
export { CrossTriggerIntegration } from './integrations/cross-trigger';
export { OpenClawPlatformAdapter } from './adapters/openclaw';
export { LobeHubPlatformAdapter } from './adapters/lobehub';

// 主入口示例
if (require.main === module) {
  console.log('LobeHub-OpenClaw Integration System');
  console.log('====================================');
  
  const config: LobeHubOpenClawConfig = {
    openclaw: {
      gatewayUrl: 'http://localhost:18789',
      workspaceDir: process.env.OPENCLAW_WORKSPACE || './workspace'
    },
    lobehub: {
      baseUrl: process.env.LOBEHUB_URL || 'http://localhost:3210'
    },
    integrations: {
      sharedMemory: true,
      sharedSkills: true,
      crossTrigger: true
    }
  };

  LobeHubOpenClaw.create(config).then(async (system) => {
    console.log('System initialized');
    
    const status = await system.status();
    console.log('Status:', status);
    
  }).catch(console.error);
}
