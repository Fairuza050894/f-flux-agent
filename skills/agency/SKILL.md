---
name: agency-agents
description: "Browse & activate 200+ specialist AI personas from Agency Agents repo."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ai-personas, agency, specialists, claude-code, cursor, copilot]
    category: ai-agents
    related_skills: [software-development, code-review, architecture]
    config:
      agency_repo_url: "https://github.com/msitarzewski/agency-agents"
      agency_local_path: "~/.hermes/skills/agency/agents"
      auto_update: true
---

# Agency Agents Integration

Access **200+ specialist AI personas** from the [Agency Agents](https://github.com/msitarzewski/agency-agents) repository — frontend wizards, backend architects, security engineers, QA specialists, and more.

## When to Use

- Need a **specialist perspective** (e.g., "review this as a security engineer")
- Want to **reduce repetitive prompting** with pre-defined expert roles
- Working with **Claude Code, Cursor, Copilot, Gemini, OpenCode** — personas are portable
- Building **multi-agent workflows** with distinct roles

## Prerequisites

- `git` for cloning/updating the repo
- Optional: `gh` CLI for starred/recommended personas

## How to Run

### List Available Personas

```
/agency list
/agency list --category engineering
/agency list --search security
```

### Activate a Persona

```
/agency use backend-architect
/agency use security-engineer --context "review auth flow"
/agency use qa-automation-lead --context "design test plan for checkout"
```

### Install Personas Locally

```
/agency install                    # Clone full repo to ~/.hermes/skills/agency/agents
/agency update                     # Pull latest personas
/agency install --category qa      # Only QA personas
```

### Create Custom Workflow

```
/agency workflow "security-review" backend-architect security-engineer qa-automation-lead
/agency run security-review --context "PR #1234"
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `/agency list [--category CAT] [--search TERM]` | Browse personas |
| `/agency use <persona> [--context TEXT]` | Activate persona for current conversation |
| `/agency install [--category CAT]` | Clone personas locally |
| `/agency update` | Update local personas |
| `/agency workflow <name> <persona1> <persona2>...` | Define multi-agent workflow |
| `/agency run <workflow> [--context TEXT]` | Execute workflow |

## Persona Categories (from Agency Agents)

| Category | Example Personas |
|----------|------------------|
| **Engineering** | backend-architect, frontend-wizard, devops-engineer, api-designer |
| **Security** | security-engineer, penetration-tester, compliance-auditor |
| **QA** | qa-automation-lead, test-architect, e2e-test-designer |
| **Design** | ui-ux-designer, design-system-architect, accessibility-expert |
| **Data** | data-engineer, ml-engineer, analytics-engineer |
| **Product** | product-manager, technical-writer, release-manager |
| **Specialized** | game-dev, gis-specialist, blockchain-engineer, spatial-computing |

## Procedure

### 1. Initial Setup

```bash
# Clone personas locally
/agency install

# Or browse remote (no clone needed)
/agency list --remote
```

### 2. Activate a Persona

When you activate a persona, Hermes will:
1. Load the persona's `.md` file (YAML frontmatter + instructions)
2. Inject it as a **skill context** (not system prompt — preserves caching)
3. The persona stays active until you `/agency clear` or switch

### 3. Multi-Agent Workflow

Define a workflow once, run many times:

```
/agency workflow "full-qa" qa-automation-lead test-architect e2e-test-designer
/agency run full-qa --context "test new payment flow"
```

Each persona in the workflow gets the context and contributes their expertise.

## Pitfalls

- **Don't activate too many personas** — each adds context tokens. Max 3-4 recommended.
- **Personas are Markdown** — they're instructions for the LLM, not executable code.
- **Remote vs Local** — `--remote` fetches from GitHub API (rate limited); local is faster.
- **Updates** — Run `/agency update` weekly for new personas.

## Verification

```bash
# Test installation
/agency list | head -20

# Test activation
/agency use backend-architect --context "design API for user service"
# Should respond with architect perspective
```

## Integration with Other Skills

- **software-development** — personas enhance code review, architecture
- **qa_automation** — qa-automation-lead persona + Veriflow trigger
- **github** — security-engineer persona for PR reviews