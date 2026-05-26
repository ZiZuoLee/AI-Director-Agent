# AI-Director-Agent
Final Course Project of Fudan University Computer Graph A

## Environment Setup

Copy `.env.example` to `.env` and fill in your OpenRouter API key:

```text
OPENROUTER_API_KEY=sk-xxx...
```

The project will load `OPENROUTER_API_KEY` from `.env` at runtime.

## LLM Prompt Workflow

The Agent Layer now builds Chinese prompt design instructions and sends them to OpenRouter.
The model is expected to return a JSON object containing fields like `shot_type`, `camera_movement`, `prompt`, `description`, and `reason`.
