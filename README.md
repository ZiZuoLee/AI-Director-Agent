# AI-Director-Agent
Final Course Project of Fudan University Computer Graph A

## LLM Prompt Workflow

The Agent Layer now builds Chinese prompt design instructions and sends them to OpenRouter.
The model is expected to return a JSON object containing fields like `shot_type`, `camera_movement`, `prompt`, `description`, and `reason`.

## Environment Setup

Copy `.env.example` to `.env` and fill in your OpenRouter API key:

```text
OPENROUTER_API_KEY=sk-xxx...
```

The project will load `OPENROUTER_API_KEY` from `.env` at runtime.

## Git Workflow

Follow this branching workflow for all development:

- Create a local feature/fix branch from `main`:

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

