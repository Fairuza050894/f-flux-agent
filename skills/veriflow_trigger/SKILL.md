---
name: veriflow-trigger
description: "Trigger Veriflow QA automation runs and retrieve cinematic reports."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, veriflow, playwright, automation, reports]
    category: qa-automation
    related_skills: [qa_automation, agency-agents]
    config:
      veriflow_base_url: "http://localhost:3000"
      veriflow_api_key: ""
      default_repo: "https://github.com/Fairuza050894/LogiTrack"
      webhook_secret: ""
---

# Veriflow Trigger Skill

Trigger **Veriflow QA automation** runs from Hermes — analyze repos, generate Playwright tests, execute in sharded runners, get cinematic reports with architecture diagrams.

## When to Use

- User says "test this repo", "run QA on...", "verifyflow...", "veriflow..."
- Need **autonomous QA pipeline**: clone → analyze → scaffold → plan → generate → heal → execute → report
- Want **cinematic reports** with Mermaid diagrams (system context, ERD, API map, UI map, coverage)
- Need **Playwright execution** via GitHub Actions or Docker runner

## Prerequisites

- **Veriflow running** locally (`npm run dev` at `http://localhost:3000`) or deployed (Vercel)
- **Veriflow API key** (if auth enabled) — set in `config.yaml` or `.env`
- **Runner** for real Playwright: GitHub Actions (recommended) or Docker
- **Repository access** — public or with token for private repos

## Configuration

```yaml
# ~/.hermes/config.yaml
skills:
  config:
    veriflow_trigger:
      veriflow_base_url: "http://localhost:3000"  # or https://your-veriflow.vercel.app
      veriflow_api_key: ""  # optional, for authenticated endpoints
      default_repo: "https://github.com/Fairuza050894/LogiTrack"
      webhook_secret: ""  # for runner callbacks
```

## How to Run

### Quick Run (Demo)

```
/veriflow run
/veriflow run --repo https://github.com/owner/repo
/veriflow run --repo https://github.com/owner/repo --name "My Project"
```

### Custom Run

```
/veriflow run --repo https://github.com/owner/repo --feature "checkout flow" --mode smoke
/veriflow run --repo https://github.com/owner/repo --feature "payment" --mode regression
```

### Monitor Progress

```
/veriflow status <run_id>
/veriflow logs <run_id>
/veriflow wait <run_id>  # Block until complete
```

### Get Report

```
/veriflow report <run_id>
/veriflow report <run_id> --format html
/veriflow report <run_id> --format markdown
```

### List Runs

```
/veriflow list
/veriflow list --project <project_id>
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `/veriflow run [--repo URL] [--name NAME] [--feature TEXT] [--mode smoke\|regression]` | Start QA run |
| `/veriflow status <run_id>` | Check run status |
| `/veriflow logs <run_id>` | Stream SSE logs |
| `/veriflow wait <run_id>` | Wait for completion |
| `/veriflow report <run_id> [--format html\|md\|json]` | Get report |
| `/veriflow list [--project ID]` | List runs |
| `/veriflow config` | Show current config |

## Veriflow Pipeline (14 Steps)

1. **Clone** — Fetch repository
2. **Analyze** — Detect stack, framework, patterns
3. **Scaffold** — Create test project structure
4. **Plan** — Design test strategy (unit, API, E2E)
5. **Generate** — Write Playwright tests (TypeScript)
6. **Heal** — Auto-fix generated tests
7. **Execute** — Run in sharded runners
8. **Results** — Collect pass/fail/flaky
9. **Report** — Generate cinematic report
10. **Diagrams** — Mermaid: D01-D09 (context, ERD, deps, API, UI, pipeline, infra, coverage)
11. **Email** — Send signed report link
12. **Notify** — Webhook/approval gates
13. **Archive** — Store artifacts
14. **Cleanup** — Prune old runs

## Report Formats

- **HTML** — Full cinematic report with interactive Mermaid diagrams
- **Markdown** — Summary for Telegram/Slack
- **JSON** — Raw data for programmatic use

## Integration with Agency Agents

Combine with `/agency use qa-automation-lead` for expert QA perspective:

```
/agency use qa-automation-lead --context "design test strategy for checkout"
/veriflow run --repo https://github.com/shop/app --feature "checkout"
```

## Pitfalls

- **Local Veriflow** needs SQLite at `/tmp/veriflow.db` (Vercel) or `./.data/veriflow.db` (local)
- **Runner** required for real Playwright — mock mode works without runner
- **Private repos** need GitHub token in Veriflow config
- **Large repos** — increase `VERIFLOW_STEP_DELAY_MS` for slower analysis
- **Telegram** — reports can be long; use `/veriflow report --format markdown` for chat

## Verification

```bash
# Test Veriflow is running
curl http://localhost:3000/api/v1/health

# Test quick run
curl -X POST http://localhost:3000/api/v1/projects/quick-run \
  -H 'content-type: application/json' \
  -d '{"repo_url":"https://github.com/Fairuza050894/LogiTrack","name":"LogiTrack"}'
```