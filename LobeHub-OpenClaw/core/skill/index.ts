/**
 * Skill Interface - Skill 规范
 *
 * 统一 Skills 定义，支持 LobeHub 与 OpenClaw Skills 共享
 */

export interface SkillParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required?: boolean;
  description: string;
  default?: any;
  enum?: string[];
}

export interface SkillOutput {
  type: 'text' | 'json' | 'file' | 'error';
  description: string;
}

export interface SkillManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author?: string;
  tags: string[];
  
  parameters: SkillParameter[];
  output: SkillOutput;
  
  // 执行配置
  timeout?: number;  // 超时时间（毫秒）
  retries?: number;  // 重试次数
  
  // 来源
  source: 'lobehub' | 'openclaw' | 'custom';
  originalId?: string;  // 如果是从其他平台导入
}

export interface SkillContext {
  eventBus: any;
  memory: any;
  config: Record<string, any>;
  userId?: string;
  sessionId?: string;
}

export type SkillHandler = (params: Record<string, any>, context: SkillContext) => Promise<any>;

export interface Skill {
  manifest: SkillManifest;
  execute: SkillHandler;
}

// Skill 加载器接口
export interface SkillLoader {
  load(id: string): Promise<Skill | null>;
  list(): Promise<SkillManifest[]>;
  uninstall(id: string): Promise<boolean>;
}

// Skill 注册表
export class SkillRegistry {
  private skills: Map<string, Skill> = new Map();

  register(skill: Skill): void {
    this.skills.set(skill.manifest.id, skill);
  }

  unregister(id: string): boolean {
    return this.skills.delete(id);
  }

  get(id: string): Skill | undefined {
    return this.skills.get(id);
  }

  list(): SkillManifest[] {
    return Array.from(this.skills.values()).map(s => s.manifest);
  }

  findByTag(tag: string): SkillManifest[] {
    return this.list().filter(s => s.tags.includes(tag));
  }
}
