---
name: x-article-reader
description: Read X (Twitter) article content from URL. Extracts article text from x.com article links using jina.ai reader. Use when you need to fetch and summarize X articles.
---

# X Article Reader

Read article content from X (Twitter) URLs.

## Usage

### Read Article from URL

```bash
# Direct article URL
curl -s "https://r.jina.ai/https://x.com/<username>/article/<article-id>"

# Or use the helper function
x_article "<x-article-url>"
```

## How It Works

1. **Extract article URL** - Get the article link from X URL
   - Format: `https://x.com/<user>/article/<id>`
   
2. **Fetch content via jina.ai** - Use jina.ai reader
   - Format: `https://r.jina.ai/https://x.com/<user>/article/<id>`

## Example

```bash
# Article URL
# https://x.com/elonmusk/article/1234567890

# Fetch content
curl -s "https://r.jina.ai/https://x.com/elonmusk/article/1234567890"
```

## Output

Returns the full article text including:
- Title
- Author
- Publication date
- Article body
- Media links (if any)

## Notes

- No API key required
- Works with public articles
- jina.ai provides free article extraction
- Response is in Markdown format
