#!/bin/bash
# Token Usage Comparison Script
# 比较全量加载 vs 按需检索的记忆消耗

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

MEMORY_FILE="$HOME/.openclaw/workspace/MEMORY.md"
LESSONS_FILE="$HOME/.openclaw/workspace/memory/lessons-learned.md"
TODAY_FILE="$HOME/.openclaw/workspace/memory/$(date +%Y-%m-%d).md"

echo "========================================="
echo "     OpenClaw Agent 记忆消耗实测"
echo "========================================="
echo ""

# 测试 MEMORY.md
test_file() {
    local file=$1
    local name=$2
    
    if [ ! -f "$file" ]; then
        echo "⚠️ 文件不存在: $file"
        return 1
    fi
    
    local size=$(wc -c < "$file")
    local lines=$(wc -l < "$file")
    local words=$(wc -w < "$file")
    local tokens=$((words * 2 / 3))
    
    echo "📄 $name"
    echo "   大小: $size bytes"
    echo "   行数: $lines"
    echo "   单词: $words"
    echo "   Token消耗: ~$tokens tokens"
    echo ""
}

# 测试不同文件
echo "=== 1. MEMORY.md (长期记忆) ==="
test_file "$MEMORY_FILE" "MEMORY.md"

echo "=== 2. lessons-learned.md (教训记录) ==="
test_file "$LESSONS_FILE" "lessons-learned.md"

if [ -f "$TODAY_FILE" ]; then
    echo "=== 3. today's memory (今日记忆) ==="
    test_file "$TODAY_FILE" "$(date +%Y-%m-%d).md"
fi

echo "========================================="
echo "       按需检索 vs 全量加载对比"
echo "========================================="
echo ""

# 全量加载 lessons-learned.md
full_words=$(wc -w < "$LESSONS_FILE")
full_tokens=$((full_words * 2 / 3))

# 按需检索 (只读取50行)
selective_lines=50
selective_words=$((selective_lines * 10))
selective_tokens=$((selective_words * 2 / 3))

echo "📊 lessons-learned.md 全量加载: ~$full_tokens tokens"
echo "📊 按需检索 (50行): ~$selective_tokens tokens"
echo ""

savings=$((full_tokens - selective_tokens))
percent=$((savings * 100 / full_tokens))

if [ "$percent" -gt 0 ]; then
    echo "✅ 节省: ~$savings tokens ($percent%)"
else
    echo "⚠️ 按需检索更少: ~$((-savings)) tokens"
fi

echo ""
echo "💡 优化建议:"
echo "  1. ✅ 避免每次会话全量加载大型记忆文件"
echo "  2. ✅ 使用 memory_search 先检索关键词"
echo "  3. ✅ 再用 memory_get 读取必要片段"
echo "  4. ✅ 每日记忆使用 memory/YYYY-MM-DD.md"
echo ""
echo "📌 最佳实践:"
echo "  - 长期偏好: 写入 MEMORY.md (53行, ~70 tokens)"
echo "  - 每日总结: 写入 memory/YYYY-MM-DD.md"
echo "  - 教训记录: 写入 lessons-learned.md"
echo "========================================="
