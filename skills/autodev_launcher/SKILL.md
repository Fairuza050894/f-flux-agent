---
name: autodev-launcher
description: "Launch AutoDev Office projects: requirement → design → code → QA → deploy → handover."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [autodev, sdlc, virtual-office, full-stack, deployment, gitea]
    category: development
    related_skills: [veriflow-trigger, software-development, github]
    config:
      autodev_base_url: "http://localhost:4000"
      autodev_dashboard_url: "http://localhost:3000"
      default_email: "user@example.com"
      mock_mode: true
---

# AutoDev Launcher Skill

Launch **AutoDev Office** projects from Hermes — a virtual developer office that turns a chat request into: requirements → task plan → design → source code → QA/security → staging deploy → email handover.

## When to Use

- User says "build me a...", "create a...", "make a website/app for..."
- Need **full SDLC automation**: intake → plan → design → code → test → deploy
- Want **staging preview URLs** with health checks
- Need **Gitea repo** + **MinIO artifacts** + **email delivery**

## Prerequisites

- **AutoDev Office running** via Docker Compose:
  ```bash
  cd /path/to/Autodev-office && docker compose up --build
  ```
- Services: Dashboard (3000), API (4000), Gitea (3001), MinIO (9000/9001), Mailpit (8025)
- **Mock mode** works without LLM keys (deterministic template projects)

## Configuration

```yaml
# ~/.hermes/config.yaml
skills:
  config:
    autodev_launcher:
      autodev_base_url: "http://localhost:4000"      # API
      autodev_dashboard_url: "http://localhost:3000" # Dashboard
      default_email: "user@example.com"
      mock_mode: true
```

## How to Run

### Create Project (Quick)

```
/autodev create "Buatkan website company profile untuk klinik gigi. Fitur profil dokter, daftar layanan, formulir kontak. Email saya demo@example.test."
```

### Create Project (Advanced)

```
/autodev create "E-commerce sederhana: produk, keranjang, checkout. Email admin@shop.test." --mode gated
/autodev create "Dashboard analytics untuk sales team. Email sales@corp.test." --mode gated --budget 50
```

### Monitor Project

```
/autodev status <project_id>
/autodev logs <project_id>
/autodev artifacts <project_id>
/autodev url <project_id>  # Get staging URL
```

### Approve Gates (for GATED_PROPOSAL / GATED_RELEASE)

```
/autodev approve <project_id> --gate proposal
/autodev approve <project_id> --gate release
/autodev reject <project_id> --gate proposal --reason "Budget exceeded"
```

### List Projects

```
/autodev list
/autodev list --status running
/autodev list --status completed
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `/autodev create "requirement text" [--mode mock\|gated] [--budget N] [--email EMAIL]` | Create project |
| `/autodev status <project_id>` | Get project status + DAG |
| `/autodev logs <project_id>` | Stream worker logs |
| `/autodev artifacts <project_id>` | List artifacts (source, QA, security) |
| `/autodev url <project_id>` | Get staging preview URL |
| `/autodev approve <project_id> --gate proposal\|release` | Approve gate |
| `/autodev reject <project_id> --gate proposal\|release --reason TEXT` | Reject gate |
| `/autodev list [--status STATUS]` | List projects |

## AutoDev Pipeline Stages

1. **Intake** — Parse requirement, extract features
2. **Plan** — Generate task DAG, assign agents
3. **Design** — Architecture, API contracts, UI mockups
4. **Implement** — Write source code (Next.js, React, etc.)
5. **QA** — Run tests (unit, integration, E2E via Veriflow)
6. **Security** — SAST, dependency scan, secrets detection
7. **Deploy** — Build Docker image, deploy to staging
8. **Health Check** — Verify /live endpoint
9. **Handover** — Email with portal link, artifacts, survey

## Project Modes

| Mode | Description |
|------|-------------|
| `mock` | Deterministic template, no LLM calls, instant (demo) |
| `gated` | Full LLM pipeline, requires approval at Proposal & Release gates |
| `proposal_only` | Stop after proposal gate, user reviews plan |

## Integration with Veriflow

AutoDev can use Veriflow for QA stage:

```
/autodev create "Build a dashboard with charts. Email me@corp.test." --mode gated
# ... AutoDev runs Veriflow internally for QA ...
/veriflow report <run_id>  # Get detailed QA report
```

## Integration with Agency Agents

Use specialist personas for AutoDev stages:

```
/agency use backend-architect --context "design API for AutoDev project"
/agency use security-engineer --context "review AutoDev security scan results"
/autodev status <project_id>
```

## Pitfalls

- **Docker required** — AutoDev runs in containers (sandbox, Gitea, MinIO, PostgreSQL, Redis)
- **8 GB RAM** minimum for full stack
- **Port conflicts** — AutoDev uses 3000, 3001, 4000, 8025, 9000, 9001
- **Mock mode** — Fast but generates template code, not custom logic
- **Gated mode** — Requires manual approval via `/autodev approve` or dashboard
- **Email** — Uses Mailpit (localhost:8025) in dev; configure SMTP for production

## Verification

```bash
# Check AutoDev API health
curl http://localhost:4000/api/v1/health

# Check Dashboard
open http://localhost:3000  # admin@autodev.local / AutoDevLocal2026!

# Test mock project creation
curl -X POST http://localhost:4000/api/v1/projects \
  -H 'content-type: application/json' \
  -d '{"brief":"Simple landing page","email":"test@example.com","mode":"mock"}'
```