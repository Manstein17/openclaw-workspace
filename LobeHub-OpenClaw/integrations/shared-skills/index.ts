/**
 * Shared Skills Integration - Skills 共享模块
 *
 * 实现 LobeHub 与 OpenClaw Skills 互操作
 */

import * as fs from 'fs';
import * as path from 'path';
import { Skill, SkillManifest, SkillRegistry } from '../core/skill';
import { EventBus, Events } from '../core/event';

export interface SharedSkillsConfig {
  lobehubSkillsDir?: string;   // LobeHub Skills/Agents 目录
  openclawSkillsDir?: string;   // OpenClaw Skills 目录
  sharedDir: string;           // 共享目录
  autoImport?: boolean;
}

export class SharedSkillsIntegration {
  private config: SharedSkillsConfig;
  private registry: SkillRegistry;
  private eventBus: EventBus;

  constructor(config: SharedSkillsConfig, eventBus: EventBus) {
    this.config = {
      autoImport: true,
      ...config,
    };
    this.registry = new SkillRegistry();
    this.eventBus = eventBus;
  }

  /**
   * 初始化
   */
  async init(): Promise<void> {
    // 确保目录存在
    this.ensureDir(this.config.sharedDir);
    if (this.config.lobehubSkillsDir) {
      this.ensureDir(this.config.lobehubSkillsDir);
    }
    if (this.config.openclawSkillsDir) {
      this.ensureDir(this.config.openclawSkillsDir);
    }

    if (this.config.autoImport) {
      await this.importAll();
    }
  }

  /**
   * 从所有来源导入 Skills
   */
  async importAll(): Promise<{ lobehub: number; openclaw: number }> {
    let lobehubCount = 0;
    let openclawCount = 0;

    // 从 LobeHub 导入
    if (this.config.lobehubSkillsDir) {
      lobehubCount = await this.importFromDir(this.config.lobehubSkillsDir, 'lobehub');
    }

    // 从 OpenClaw 导入
    if (this.config.openclawSkillsDir) {
      openclawCount = await this.importFromDir(this.config.openclawSkillsDir, 'openclaw');
    }

    return { lobehub: lobehubCount, openclaw: openclawCount };
  }

  /**
   * 从目录导入 Skills
   */
  private async importFromDir(dir: string, source: 'lobehub' | 'openclaw'): Promise<number> {
    if (!fs.existsSync(dir)) return 0;

    let count = 0;

    try {
      const files = fs.readdirSync(dir, { recursive: true });

      for (const file of files) {
        const filePath = path.join(dir, file);
        
        if (fs.statSync(filePath).isDirectory()) {
          count += await this.importFromDir(filePath, source);
          continue;
        }

        // LobeHub 可能用 .ts, .js, .json
        // OpenClaw 用 .ts
        if (!file.match(/\.(ts|js|json)$/)) continue;

        try {
          const skill = await this.parseSkillFile(filePath, source);
          if (skill) {
            this.registry.register(skill);
            count++;
          }
        } catch (error) {
          console.error(`Failed to parse skill ${filePath}:`, error);
        }
      }
    } catch (error) {
      console.error(`Failed to read directory ${dir}:`, error);
    }

    return count;
  }

  /**
   * 解析 Skill 文件
   */
  private async parseSkillFile(filePath: string, source: 'lobehub' | 'openclaw'): Promise<Skill | null> {
    const content = fs.readFileSync(filePath, 'utf-8');

    // 尝试解析 JSON（OpenClaw skill.json）
    try {
      const json = JSON.parse(content);
      if (json.manifest || json.id) {
        return {
          manifest: json.manifest || json,
          execute: async () => ({ error: 'Not implemented' }),
        };
      }
    } catch {
      // 不是 JSON，尝试 TypeScript/JavaScript
    }

    // 尝试从文件提取 metadata
    const fileName = path.basename(filePath, path.extname(filePath));
    const manifest: SkillManifest = {
      id: `${source}-${fileName}`,
      name: fileName,
      version: '1.0.0',
      description: `Imported from ${source}`,
      tags: [source, 'imported'],
      parameters: [],
      output: { type: 'text', description: 'Skill output' },
      source,
    };

    return {
      manifest,
      execute: async () => ({ error: 'Not implemented' }),
    };
  }

  /**
   * 导出 Skill 到共享目录
   */
  async export(skill: Skill, targetDir?: string): Promise<string> {
    const dir = targetDir || this.config.sharedDir;
    this.ensureDir(dir);

    const filePath = path.join(dir, `${skill.manifest.id}.json`);
    const content = JSON.stringify(skill.manifest, null, 2);

    fs.writeFileSync(filePath, content);
    this.registry.register(skill);

    return filePath;
  }

  /**
   * 获取所有 Skills 列表
   */
  list(): SkillManifest[] {
    return this.registry.list();
  }

  /**
   * 执行 Skill
   */
  async execute(skillId: string, params: Record<string, any>): Promise<any> {
    const skill = this.registry.get(skillId);
    if (!skill) {
      throw new Error(`Skill not found: ${skillId}`);
    }

    const result = await skill.execute(params, {
      eventBus: this.eventBus,
      memory: null,
      config: {},
    });

    // 发布事件
    await this.eventBus.publish({
      type: Events.Common.SKILL_INVOKED,
      source: 'shared-skills',
      payload: { skillId, result },
    });

    return result;
  }

  /**
   * 查找 Skills
   */
  find(options: {
    tags?: string[];
    source?: 'lobehub' | 'openclaw' | 'all';
    query?: string;
  }): SkillManifest[] {
    let skills = this.registry.list();

    if (options.source && options.source !== 'all') {
      skills = skills.filter(s => s.source === options.source);
    }

    if (options.tags && options.tags.length > 0) {
      skills = skills.filter(s => 
        options.tags!.some(t => s.tags.includes(t))
      );
    }

    if (options.query) {
      const lower = options.query.toLowerCase();
      skills = skills.filter(s =>
        s.name.toLowerCase().includes(lower) ||
        s.description.toLowerCase().includes(lower) ||
        s.tags.some(t => t.toLowerCase().includes(lower))
      );
    }

    return skills;
  }

  /**
   * 同步 Skills 到 LobeHub 格式
   */
  async exportToLobeHubFormat(skillId: string): Promise<any> {
    const skill = this.registry.get(skillId);
    if (!skill) {
      throw new Error(`Skill not found: ${skillId}`);
    }

    // 转换为 LobeHub Agent 格式
    return {
      name: skill.manifest.name,
      system_prompt: skill.manifest.description,
      model: 'gpt-4',
      tags: skill.manifest.tags,
      tools: [],
    };
  }

  /**
   * 同步 Skills 到 OpenClaw 格式
   */
  async exportToOpenClawFormat(skillId: string): Promise<any> {
    const skill = this.registry.get(skillId);
    if (!skill) {
      throw new Error(`Skill not found: ${skillId}`);
    }

    // 转换为 OpenClaw Skill 格式
    return {
      id: skill.manifest.id,
      name: skill.manifest.name,
      description: skill.manifest.description,
      tags: skill.manifest.tags,
      parameters: skill.manifest.parameters,
      timeout: skill.manifest.timeout || 30000,
    };
  }

  /**
   * 获取 Stats
   */
  getStats(): { 
    total: number; 
    bySource: Record<string, number>;
    byTag: Record<string, number>;
  } {
    const skills = this.registry.list();
    const bySource: Record<string, number> = {};
    const byTag: Record<string, number> = {};

    skills.forEach(s => {
      bySource[s.source] = (bySource[s.source] || 0) + 1;
      s.tags.forEach(t => {
        byTag[t] = (byTag[t] || 0) + 1;
      });
    });

    return { total: skills.length, bySource, byTag };
  }

  /**
   * 确保目录存在
   */
  private ensureDir(dir: string): void {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }
}

/**
 * OpenClaw Skill 转换器
 */
export class OpenClawSkillConverter {
  /**
   * OpenClaw Skill JSON 转换为标准格式
   */
  static toStandard(openclawSkill: any): SkillManifest {
    return {
      id: openclawSkill.id || openclawSkill.name,
      name: openclawSkill.name,
      version: openclawSkill.version || '1.0.0',
      description: openclawSkill.description || '',
      tags: [...(openclawSkill.tags || []), 'openclaw', 'imported'],
      parameters: openclawSkill.parameters || [],
      output: openclawSkill.output || { type: 'text', description: '' },
      timeout: openclawSkill.timeout,
      retries: openclawSkill.retries,
      source: 'openclaw',
      originalId: openclawSkill.id,
    };
  }

  /**
   * 标准格式转换为 OpenClaw Skill JSON
   */
  static fromStandard(skill: SkillManifest): any {
    return {
      id: skill.id,
      name: skill.name,
      version: skill.version,
      description: skill.description,
      tags: skill.tags.filter(t => t !== 'openclaw' && t !== 'imported'),
      parameters: skill.parameters,
      output: skill.output,
      timeout: skill.timeout,
      retries: skill.retries,
    };
  }
}

/**
 * LobeHub Agent 转换器
 */
export class LobeHubAgentConverter {
  /**
   * LobeHub Agent 转换为标准格式
   */
  static toStandard(agent: any): SkillManifest {
    return {
      id: `lobehub-${agent.id}`,
      name: agent.name,
      version: '1.0.0',
      description: agent.system_prompt || agent.description || '',
      tags: [...(agent.tags || []), 'lobehub', 'imported'],
      parameters: [],
      output: { type: 'text', description: 'Agent response' },
      source: 'lobehub',
      originalId: agent.id,
    };
  }

  /**
   * 标准格式转换为 LobeHub Agent
   */
  static fromStandard(skill: SkillManifest): any {
    return {
      id: skill.manifest.originalId,
      name: skill.manifest.name,
      system_prompt: skill.manifest.description,
      model: 'gpt-4',
      tags: skill.manifest.tags.filter(t => t !== 'lobehub' && t !== 'imported'),
      tools: [],
    };
  }
}
