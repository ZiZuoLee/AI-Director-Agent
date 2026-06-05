# AI-Director-Agent
Final Course Project of Fudan University Computer Graph A

## LLM Prompt Workflow

The Agent Layer builds Chinese prompt design instructions and sends them to a Chat Completions-compatible API.
By default it uses OpenRouter, but you can override the URL/model/key locally in `.env` for testing.
The model is expected to return a JSON object containing fields like `shot_type`, `camera_movement`, `prompt`, `description`, and `reason`.

## Generation Layer

The image-generation pipeline is separated behind a stable interface and currently uses the ZenMux Vertex AI image-generation API via the `google-genai` client.

Core files:

- `prompt_gen.py`: converts planner shots into validated diffusion prompt specs
- `generate.py`: single public entry point for image generation
- `generation_types.py`: shared schemas, config, and validation
- `backends/zenmux_api.py`: ZenMux Gemini image generation backend
- `test_zenmux_api.py`: direct smoke test that bypasses the parser/planner/LLM stack

Example usage:

```python
from planner import plan_shots
from generate import build_generation_plan, generate_images

plan = plan_shots("主角在黑暗的城市小巷中奔跑，被神秘身影追赶。", count=3)

prompt_specs = build_generation_plan(
    plan["shots"],
    config={
        "backend": "zenmux_api",
        "model_id": "google/gemini-2.5-flash-image",
        "zenmux_env_path": "zenmux.env",
        "output_dir": "images",
        "width": 1024,
        "height": 1024,
        "zenmux_image_size": "1K",
        "zenmux_seed": 20260605,
    },
)

images = generate_images(
    plan["shots"],
    config={
        "backend": "zenmux_api",
        "model_id": "google/gemini-2.5-flash-image",
        "zenmux_env_path": "zenmux.env",
        "output_dir": "images",
    },
)
```

To change models, update `model_id` in config to any ZenMux Vertex image model you want to try.

The API key is read from `ZENMUX_API_KEY` in the environment or from `zenmux.env`.

## Environment Setup

Copy `.env.example` to `.env` and fill in your OpenRouter API key:

```text
OPENROUTER_API_KEY=sk-xxx...
```

The project will load `OPENROUTER_API_KEY` from `.env` at runtime.

## Git Workflow

Follow this branching workflow for all development:

- Create a local feature/fix branch from `pre`:

```bash
git checkout -b feature/your-feature
```

- Implement changes and commit locally. Push the branch to the remote:

```bash
git push -u origin feature/your-feature
```

- Open a Pull Request (PR) / Merge Request (MR) from your branch into the `pre` branch (not into `main`).
- After review and CI on `pre`, merge `pre` into `main` when the `pre` branch is considered stable.

Typical high-level sequence:

```bash
# make a feature branch
git checkout -b feature/awesome
git push -u origin feature/awesome
# open PR into 'pre' (via your Git host)
# after PR review and merge into 'pre'
git checkout main
git pull origin main
git merge origin/pre
git push origin main
```

Notes:
- Keep commits focused and small; open PRs against `pre` for review.
- Do not push unfinished work to `main`; use `pre` as the integration branch.
- Create a local backup branch before any destructive history rewrite: `git branch backup/whatever`.
