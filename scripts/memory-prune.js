#!/usr/bin/env node
/**
 * Memory Pruning Script
 *
 * 淘汰规则：
 * - P2: 超过 30 天 → 归档
 * - P1: 超过 90 天 → 归档
 * - P0: 永不淘汰
 *
 * 使用方式：
 *   node memory-prune.js --dry-run    # 预览模式
 *   node memory-prune.js              # 执行清理
 *
 * 定时任务建议：
 *   0 2 * * * cd /path/to/workspace && node memory-prune.js
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  // 记忆文件根目录（向上找一层）
  memoryDir: path.join(__dirname, '..', 'memory'),

  // 归档目录
  archiveDir: path.join(__dirname, '..', 'memory', 'archive'),

  // 淘汰阈值（天）
  thresholds: {
    P2: 30,
    P1: 90,
    P0: Infinity
  },

  // 要跳过的目录（不搜索）
  skipDirs: ['archive', 'node_modules', '.git']
};

// 计算天数差
function daysDiff(dateStr) {
  const today = new Date();
  const entryDate = new Date(dateStr);
  const diffTime = Math.abs(today - entryDate);
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// 解析单文件的记忆条目
function parseFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const entries = [];

  // 匹配 **[P2][2026-02-09]** 或 [P2][2026-02-09]
  const regex = /\*{0,1}\[P([012])\]\[(\d{4}-\d{2}-\d{2})\]\*{0,1}/g;
  const matches = [...content.matchAll(regex)];

  matches.forEach(match => {
    entries.push({
      priority: 'P' + match[1],
      date: match[2],
      content: match[0]
    });
  });

  return entries;
}

// 扫描目录获取所有文件
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

// 淘汰逻辑
function pruneMemories(dryRun = true) {
  console.log(`\n🧠 Memory Pruning Script`);
  console.log(`========================`);
  console.log(`Mode: ${dryRun ? 'DRY-RUN (预览)' : 'EXECUTING (执行)'}\n`);

  const files = scanFiles(CONFIG.memoryDir);
  const toArchive = [];
  const stats = { P0: 0, P1: 0, P2: 0, skipped: 0 };

  files.forEach(file => {
    const entries = parseFile(file);
    const relPath = path.relative(CONFIG.memoryDir, file);

    entries.forEach(entry => {
      const days = daysDiff(entry.date);
      const threshold = CONFIG.thresholds[entry.priority];

      if (days > threshold) {
        toArchive.push({
          file: relPath,
          priority: entry.priority,
          date: entry.date,
          days: days
        });
        stats[entry.priority]++;
      } else {
        stats.skipped++;
      }
    });
  });

  // 按日期排序（最旧的优先）
  toArchive.sort((a, b) => new Date(a.date) - new Date(b.date));

  // 打印统计
  console.log(`📊 Memory Entries Found:`);
  console.log(`   Total: ${stats.P0 + stats.P1 + stats.P2 + stats.skipped}`);
  console.log(`   P0 (核心): ${stats.skipped} 条（有效期内）`);
  console.log(`   P1 (阶段): ${stats.P1} 条需归档`);
  console.log(`   P2 (临时): ${stats.P2} 条需归档`);
  console.log(`\n📁 Files scanned: ${files.length}`);

  if (toArchive.length === 0) {
    console.log(`\n✅ 没有需要归档的记忆条目`);
    return;
  }

  // 预览或执行
  console.log(`\n🔄 ${dryRun ? 'Will archive' : 'Archiving'} ${toArchive.length} entries:\n`);

  toArchive.slice(0, 15).forEach((item, i) => {
    console.log(`   ${i + 1}. [${item.priority}][${item.date}] ${item.file} (${item.days}天前)`);
  });

  if (toArchive.length > 15) {
    console.log(`   ... and ${toArchive.length - 15} more`);
  }

  if (dryRun) {
    console.log(`\n💡 Run without --dry-run to actually archive these entries`);
    return;
  }

  // 实际归档
  if (!fs.existsSync(CONFIG.archiveDir)) {
    fs.mkdirSync(CONFIG.archiveDir, { recursive: true });
  }

  toArchive.forEach(item => {
    const archiveFile = path.join(CONFIG.archiveDir, `pruned-${item.date}.md`);
    const lineContent = `[${item.priority}][${item.date}] | ${item.file}`;

    fs.appendFileSync(archiveFile, lineContent + '\n');
  });

  console.log(`\n✅ 已归档 ${toArchive.length} 条到 ${CONFIG.archiveDir}/`);

  // 写入归档日志
  const logFile = path.join(CONFIG.archiveDir, 'prune-log.md');
  const logContent = `\n## ${new Date().toISOString().split('T')[0]}\n`;
  fs.appendFileSync(logFile, logContent);
}

// 主入口
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run') || args.includes('-n');

pruneMemories(dryRun);
