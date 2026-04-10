# 🏗️ DeerFlow Agent Enforcer — Architecture

## Overview

DeerFlow Agent Enforcer is a **multi-layer enforcement framework** that constrains AI coding agent behavior through configuration files, git hooks, CI/CD pipelines, and a Python-based enforcement engine.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     USER / DEVELOPER                              │
│                    (triggers AI agent task)                       │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│               LAYER 1: AI AGENT INSTRUCTIONS                     │
│  ┌─────────────┐ ┌──────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ .cursorrules│ │ CLAUDE.md│ │  COPILOT   │ │  .ai/        │  │
│  │  (Cursor)   │ │ (Claude) │ │  .md       │ │  AGENTS.md   │  │
│  └──────┬──────┘ └────┬─────┘ └─────┬──────┘ └──────┬───────┘  │
│         └──────────────┴────────────┴───────────────┘           │
│                     22 RULES LOADED                               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│               LAYER 2: DEERFLOW CORE ENGINE                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │   Orchestrator  │  │  Skill Registry  │  │ Context Mgr   │  │
│  │                 │  │                  │  │               │  │
│  │ • Pipeline      │  │ • 6 Skills       │  │ • Decisions   │  │
│  │ • Config Mgmt   │  │ • Progressive    │  │ • Task Memory │  │
│  │ • Rule Engine   │  │   Loading        │  │ • Checkpoints │  │
│  └────────┬────────┘  └──────────────────┘  └───────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              QUALITY GATE ENGINE                          │    │
│  │  Lint │ TypeCheck │ Tests │ Build │ Security │ A11y      │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│               LAYER 3: GIT HOOKS                                 │
│  ┌──────────────┐                    ┌──────────────────┐        │
│  │  pre-commit  │                    │   pre-push       │        │
│  │  6 gates     │                    │   4 gates        │        │
│  └──────────────┘                    └──────────────────┘        │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│               LAYER 4: CI/CD PIPELINE                            │
│  ┌──────────────────────┐  ┌──────────────────────────────┐     │
│  │  Quality Gate        │  │  Security Scan               │     │
│  │  Workflow            │  │  Workflow                    │     │
│  │  (5 automated gates) │  │  (deps + secrets + OWASP)    │     │
│  └──────────────────────┘  └──────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Orchestrator (`orchestrator.py`)

The main engine that coordinates all enforcement:
- **DeerFlowConfig**: Loads configuration from `deerflow.yaml`
- **RuleEngine**: Evaluates code against prohibited patterns
- **PipelineOrchestrator**: Manages the 7-stage enforcement pipeline
- **DeerFlowEngine**: Main entry point combining all components

### 2. Skill Registry (`skill_registry.py`)

Progressive skill loading system (inspired by DeerFlow architecture):
- **SkillDefinition**: Defines a skill with rules, constraints, tools, validation
- **SkillRegistry**: Manages available and active skills
- Skills are loaded progressively — only what's needed, when it's needed

### 3. Quality Gate Engine (`quality_gate.py`)

Automated quality checks:
- **12 built-in checks**: lint, type_check, unit_tests, build, security_audit, etc.
- **Gate runners**: pre_commit (6 gates), pre_push (4 gates), continuous (3 gates)
- Returns structured CheckResult with pass/fail and auto-fix suggestions

### 4. Context Manager (`context_manager.py`)

Prevents context drift in long conversations:
- **Decision tracking**: Records architecture decisions with rationale
- **Task memory**: Tracks task progress, files modified, errors encountered
- **Checkpoint persistence**: Saves/loads state from disk
- **Context summary**: Generates XML-formatted summary for AI agents

## Pipeline Stages

```
analyze → plan → implement → test → verify → validate → complete
```

Each stage has quality gates that must pass before advancing. If any gate fails, the pipeline is BLOCKED.

## Enforcement Levels

| Level | Description | Behavior |
|-------|-------------|----------|
| **strict** | Zero tolerance | Blocks on any violation |
| **moderate** | Balanced | Blocks on critical, warns on others |
| **relaxed** | Advisory | Reports but doesn't block |

## Design Principles

1. **Defense in Depth**: 5 layers of enforcement, no single point of failure
2. **Progressive Loading**: Skills and checks loaded on demand
3. **Fail-Safe**: Default to blocking when uncertain
4. **Minimal Intrusion**: Configuration files only — no build-time dependencies
5. **Universal Compatibility**: Works with ANY AI agent through multiple config formats
