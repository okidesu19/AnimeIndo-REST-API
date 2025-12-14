#!/usr/bin/env bash
# Helper script to show example env vars for proxy/scraper providers
# Usage: source ./scripts/setup_scraper_env.sh

cat <<'EOF'
Example environment variable settings (choose one method):

1) Use a residential/rotating proxy (example):

export PROXY_URL="http://user:pass@proxy-host:port"
# or
export BRIGHTDATA_PROXY="http://username:password@brd.proxy.example:port"

2) Use ScraperAPI (fallback):

export SCRAPERAPI_KEY="your_scraperapi_key_here"

3) Use ScrapingBee (fallback):

export SCRAPINGBEE_KEY="your_scrapingbee_key_here"

Quick local test (after exporting one of the above):

uvicorn main:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/api/krm/genres/
EOF

# Optional: print current env vars
echo "Current relevant env vars:"
env | egrep 'PROXY_URL|BRIGHTDATA_PROXY|SCRAPERAPI_KEY|SCRAPINGBEE_KEY' || true
