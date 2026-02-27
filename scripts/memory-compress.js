#!/usr/bin/env node
/**
 * Memory Log Compression Script
 *
 * 压缩策略：
 * - 7 天以内的日志：原样保留
 * - 超过 7 天的日志：提取精华 → 追加到 summary → 原文归档
 * - 压缩目标：7 个日志 → 不超过 20 行精华
 *
 * 使用方式：
 *   node memory-compress.js --dry-run    # 预览模式
 *   node memory-compress.js              # 执行压缩
 *
 * 定时任务建议：
 *   0 3 * * 0 cd /path/to/workspace && node memory-compress.js
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  // 记忆文件根目录
  memoryDir: path.join(__dirname, '..', 'memory'),

  // 每日日志目录
  dailyDir: path.join(__dirname, '..', 'memory', 'daily'),

  // 归档目录
  archiveDir: path.join(__dirname, '..', 'memory', 'archive'),

  // 精华摘要文件
  summaryFile: path.join(__dirname, '..', 'memory', 'projects', 'log-summaries.md'),

  // 保留天数（7天内的日志不压缩）
  keepDays: 7,

  // 压缩后最大行数
  maxSummaryLines: 20,

  // 要跳过的目录
  skipDirs: ['archive', 'node_modules', '.git']
};

// 检查文件是否超过 N 天
function daysOld(filePath) {
  const stat = fs.statSync(filePath);
  const fileDate = new Date(stat.mtime);
  const today = new Date();
  const diffTime = Math.abs(today - fileDate);
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// 简单规则提取精华（无 AI 时的降级方案）
function extractHighlights(content, fileDate) {
  const lines = content.split('\n');
  const highlights = [];

  // 规则：提取包含关键词的行
  const keywords = [
    'P0', 'P1', 'P2',          // 优先级标签
    '更新', '修改', '修复',    // 变更
    '创建', '新增', '完成',    // 成果
    '教训', '错误', '问题',    // 问题
    '配置', '设置', '安装',    // 配置
    '##', '###', '**'         // 标题/重点
  ];

  lines.forEach(line => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('*')) return;
    if (trimmed.startsWith('---')) return;

    // 保留带 P 标签的行
    if (/\[P[012]\]/.test(trimmed)) {
      if (!highlights.includes(trimmed)) {
        highlights.push(trimmed);
      }
    }

    // 保留标题
    if (/^#{1,3}\s/.test(trimmed)) {
      if (!highlights.includes(trimmed)) {
        highlights.push(trimmed);
      }
    }
  });

  // 如果提取太少，保留前几行
  if (highlights.length < 3) {
    lines.slice(0, 10).forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('*') && !trimmed.startsWith('---')) {
        if (!highlights.includes(trimmed)) {
          highlights.push(trimmed.substring(0, 100)); // 截断长行
        }
      }
    });
  }

  return highlights.slice(0, CONFIG.maxSummaryLines);
}

// AI 提取（需要 API key）
async function extractWithAI(content, fileDate) {
  // 如果有 OPENAI_API_KEY 或 ANTHROPIC_API_KEY，调用 AI
  const apiKey = process.env.OPENAI_API_KEY || process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    console.log(`   💡 设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 可启用 AI 智能提取`);
    return extractHighlights(content, fileDate);
  }

  // TODO: 实现 AI API 调用
  // 这里留个占位符
  console.log(`   ⚠️ AI 提取功能待实现，先用规则提取`);
  return extractHighlights(content, fileDate);
}

// 扫描目录
function scanFiles(dir, files = []) {
  if (!fs.existsSync(dir)) return files;

  const items = fs.readdirSync(dir);
  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!CONFIG.skipDirs.includes(item)) {
        scanFiles(fullPath, files);
      }
    } else if (item.endsWith('.md')) {
      files.push(fullPath);
    }
  });

  return files;
}

// 压缩逻辑
async function compressLogs(dryRun = true) {
  console.log(`\n📦 Memory Log Compression Script`);
  console.log(`=================================`);
  console.log(`Mode: ${dryRun ? 'DRY-RUN (预览)' : 'EXECUTING (执行)'}\n`);

  if (!fs.existsSync(CONFIG.dailyDir)) {
    console.log(`✅ 没有 daily 目录，无需压缩`);
    return;
  }

  const files = scanFiles(CONFIG.dailyDir);
  const toCompress = [];

  // 找出超过 7 天的日志
  files.forEach(file => {
    const days = daysOld(file);
    if (days > CONFIG.keepDays) {
      toCompress.push({
        path: file,
        days: days,
        date: path.basename(file, '.md')
      });
    }
  });

  if (toCompress.length === 0) {
    console.log(`✅ 没有超过 ${CONFIG.keepDays} 天的日志，无需压缩`);
    return;
  }

  console.log(`📊 Found ${toCompress.length} files older than ${CONFIG.keepDays} days:\n`);

  toCompress.sort((a, b) => a.days - b.days);

  toCompress.slice(0, 10).forEach((item, i) => {
    console.log(`   ${i + 1}. ${item.date} (${item.days} days old)`);
  });

  if (toCompress.length > 10) {
    console.log(`   ... and ${toCompress.length - 10} more`);
  }

  if (dryRun) {
    console.log(`\n💡 Run without --dry-run to actually compress these logs`);
    return;
  }

  // 执行压缩
  let totalLinesExtracted = 0;

  for (const item of toCompress) {
    const content = fs.readFileSync(item.path, 'utf-8');
    const highlights = await extractWithAI(content, item.date);

    if (highlights.length > 0) {
      // 追加到 summary 文件
      const summaryEntry = `\n## ${item.date} (压缩自 ${item.days} 天前)\n${highlights.join('\n')}\n`;

      fs.appendFileSync(CONFIG.summaryFile, summaryEntry);
      totalLinesExtracted += highlights.length;
    }

    // 移到 archive
    const archivePath = path.join(CONFIG.archiveDir, `daily-${item.date}.md`);
    fs.renameSync(item.path, archivePath);

    console.log(`   ✅ ${item.date}: ${highlights.length} lines extracted, archived`);
  }

  console.log(`\n✅ 压缩完成：${toCompress.length} 个文件`);
  console.log(`   提取精华: ${totalLinesExtracted} 行`);
  console.log(`   归档位置: ${CONFIG.archiveDir}/`);
  console.log(`   摘要追加: ${CONFIG.summaryFile}`);
}

// 主入口
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run') || args.includes('-n');

compressLogs(dryRun);
