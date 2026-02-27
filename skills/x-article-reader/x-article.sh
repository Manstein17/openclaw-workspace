#!/bin/bash
# X Article Reader - Fetch article content from x.com URLs

# Extract article ID from various X URL formats
extract_article_url() {
    local input="$1"
    
    # Handle different URL formats
    # https://x.com/<user>/article/<id>
    # https://twitter.com/<user>/article/<id>
    
    # Check if it's already an article URL
    if echo "$input" | grep -q "x.com/.*/article/"; then
        # Extract the article part
        echo "$input" | grep -oE "https://x\.com/[a-zA-Z0-9_]+/article/[0-9]+"
        return 0
    fi
    
    # If it's just a regular tweet/article URL, use as-is
    echo "$input"
}

# Main function to fetch X article
x_article() {
    local url="$1"
    
    if [ -z "$url" ]; then
        echo "Usage: x_article <x-article-url>"
        echo "Example: x_article https://x.com/username/article/1234567890"
        return 1
    fi
    
    # Extract clean article URL
    local article_url=$(extract_article_url "$url")
    
    if [ -z "$article_url" ]; then
        echo "Error: Invalid X article URL"
        echo "Expected format: https://x.com/<user>/article/<id>"
        return 1
    fi
    
    echo "Fetching article from: $article_url"
    echo "---"
    
    # Fetch via jina.ai
    local jina_url="https://r.jina.ai/https://${article_url#https://}"
    curl -s "$jina_url"
}

# If script is run directly, use arguments
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    x_article "$@"
fi
