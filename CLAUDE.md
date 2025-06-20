- Remember to think step by step, and explicitly review the logs to get data on what happened. If there is not enough information in the logs add more, but to save make use of debug, verbose or limited logs or standard logging info.
- Before you start making code ask clarifying questions to help you design if you are not sure about something.
- Build a set of test cases that you build upon so that you can run regression after each step.  But if things change ask if that still should be tested.
- Build things as simple as possible and build in steps such that you can build the MVP, test it with regression test and then have the user test it.  Build automated testcases instead of you testing it each time. And build more comprehensive test cases and tools over time.

# RAG System Quick Reference

## Architecture
- FastAPI backend (port 8001), ChromaDB (port 8000), Next.js UI (port 3004)
- Models: `/src/core/models.py`, Search: `/src/search/search_engine.py`, UI: `/src/ui/modern/ui.tsx`

## Key Components
- **Citations**: `Citation` model with text/document/relevancy_score for SOC2 compliance
- **Top-K config**: UI panel at line 667, default 5, range 1-50
- **System prompts**: Use `AskRequest.system_prompt` field - NEVER prepend to user question

## Critical Fixes
- **Markdown rendering**: Send system_prompt separately, not combined with question
- **Port conflicts**: API on 8001 (ChromaDB uses 8000)
- **Irrelevant citations**: Smart filtering in search_engine.py:214-218

## Quick Tests
```bash
curl -s http://localhost:8001/health
curl -s -X POST http://localhost:8001/api/ask -H "Content-Type: application/json" -d '{"question": "test", "system_prompt": "Reply in markdown."}'
```
