# Dual Scraper Methods (Requests + Playwright) Implementation

Status: COMPLETED ✅

## Summary

- All Kuramanime endpoints now support `?request=requests` (default) or `?request=playwright`
- Playwright versions for: genres, animeView, schedule, search, propertyGenre, animeDetail, streamingUrl
- Unified dispatchers in kuramanime.py
- Routes updated with Query param and async calls
- fetchMethod included in responses for playwright
- Streaming path merged (no separate /playwright)

## Examples

```
GET /api/krm/genres?request=playwright
GET /api/krm/view/Ongoing?request=playwright
GET /api/krm/anime/{id}/{slug}/episode/{ep}?request=playwright
```

## Next

- Test with `uvicorn main:app --reload`
- Deploy-ready (Dockerfile.playwright exists)
- Monitor performance (playwright slower/heavier)

All steps completed.
