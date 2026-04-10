# 🦌 DeerFlow Agent Enforcer

> **Strict AI Agent Quality Framework v2.0.0**
> Based on [DeerFlow](https://github.com/bytedance/deer-flow) by ByteDance — Agentic Workflow & Agent Skill System

---

## 🎯 What Is This?

DeerFlow Agent Enforcer is a **single-repo enforcement framework** that makes ANY AI coding agent follow strict, production-grade rules. One `git clone` and every AI agent in your project — Cursor, Claude, Copilot, Windsurf, Zed, Devin, Amazon Q, or any other — is forced to:

- ✅ Write **real, complete code** — no mocks, stubs, or TODOs
- ✅ **Plan before coding** — architecture first, always
- ✅ **Never delete files** without explicit confirmation
- ✅ **Verify APIs against documentation** — no hallucination
- ✅ **Write tests** for every function, component, and endpoint
- ✅ **Handle errors comprehensively** — no unhandled promises
- ✅ **Build complete artifacts** — no suspiciously small outputs
- ✅ **Follow security best practices** — no hardcoded secrets
- ✅ **Produce professional UI** — responsive, accessible, consistent
- ✅ **Maintain context** — never lose track of requirements

## ⚡ Quick Start

```bash
# 1. Clone this repo into your project (or use as a template)
git clone https://github.com/YOUR_USERNAME/deerflow-agent-enforcer.git

# 2. Copy the enforcement files to your project
cp -r deerflow-agent-enforcer/.cursorrules /your-project/
cp -r deerflow-agent-enforcer/CLAUDE.md /your-project/
cp -r deerflow-agent-enforcer/.ai/ /your-project/
cp -r deerflow-agent-enforcer/.github/ /your-project/
cp -r deerflow-agent-enforcer/deerflow-core/ /your-project/
cp -r deerflow-agent-enforcer/deerflow.yaml /your-project/
cp -r deerflow-agent-enforcer/hooks/ /your-project/
cp -r deerflow-agent-enforcer/scripts/ /your-project/

# 3. Run setup
cd /your-project
bash scripts/setup.sh

# 4. Verify installation
bash scripts/validate.sh

# 5. Done. All AI agents are now enforced.
```

## 🏗️ Architecture

```
deerflow-agent-enforcer/
├── 📋 .cursorrules              # Cursor IDE rules (15 core rules)
├── 📋 CLAUDE.md                 # Claude Code/Desktop rules
├── 📋 .github/
│   ├── copilot-instructions.md  # GitHub Copilot rules
│   └── workflows/
│       ├── deerflow-quality-gate.yml    # CI quality pipeline (5 gates)
│       └── deerflow-security-scan.yml   # Security audit pipeline
├── 📋 .ai/
│   ├── AGENTS.md                # Universal rules (ALL agents)
│   ├── SYSTEM_PROMPT.md         # Base system prompt
│   └── WINDSURF.md              # Windsurf/Zed/Tabnine rules
├── 🧠 deerflow-core/            # Core enforcement engine
│   └── engine/
│       ├── orchestrator.py      # Main engine (config, rules, pipeline)
│       ├── skill_registry.py    # Progressive skill loading system
│       ├── quality_gate.py      # 12 automated quality checks
│       └── context_manager.py   # Context persistence & decision tracking
├── ⚙️ deerflow.yaml             # Main configuration
├── 🪝 hooks/
│   ├── pre-commit               # Git pre-commit (6 quality gates)
│   ├── pre-push                 # Git pre-push (4 quality gates)
│   └── agent-guard.sh           # Runtime agent guard
├── 🔧 scripts/
│   ├── setup.sh                 # One-command setup
│   └── validate.sh              # Full validation check
├── 📚 docs/                     # Documentation
│   ├── ARCHITECTURE.md          # Architecture deep-dive
│   ├── RULES.md                 # Complete rules reference
│   └── SKILLS.md                # Agent skill system
└── 📜 LICENSE                   # MIT License
```

## 🔴 The 22 Problems This Solves

| # | Problem | DeerFlow Solution |
|---|---------|-------------------|
| 1 | AI writes bad code | Rule R05: No mocks, real implementations only |
| 2 | Messy architecture | Rule R06: Architecture before implementation |
| 3 | Poor algorithms | Rule R12: Performance optimization mandatory |
| 4 | Ripple bugs (fix one, break another) | Rule R07: Minimal surgical changes |
| 5 | Library conflicts | Rule R02: Dependency safety checks |
| 6 | Mock data everywhere | Rule R05: Prohibited patterns detection |
| 7 | Deletes important directories | Rule R01: File preservation with backup |
| 8 | Build is tiny (missing assets) | Rule R03: Build size verification |
| 9 | No testing tools | Rule R10: Mandatory testing for all code |
| 10 | No MCP/tools | Skill system with tool requirements |
| 11 | Ugly UI | Rule R14: Professional UI standards |
| 12 | Disconnected components | Rule R06: Component hierarchy planning |
| 13 | Code doesn't run | Quality gates block incomplete work |
| 14 | Misunderstands requirements | Phase 1: Deep analysis before coding |
| 15 | No web search / wrong info | Rule R07: Evidence-based development |
| 16 | Takes shortcuts | Rule R22: No shortcuts, zero tolerance |
| 17 | No theory → practice | Architecture-first with ADR documentation |
| 18 | Poor security | Rule R09: Security-first enforcement |
| 19 | Infinite loops | Rule R08: Loop & state safety checks |
| 20 | Loses proxy/VPN | Context persistence prevents drift |
| 21 | Long context → forgets | Context manager with checkpoint recovery |
| 22 | Wastes tokens | Quality gates prevent unnecessary rework |

## 🧠 DeerFlow Agentic Workflow

Based on ByteDance's DeerFlow architecture:

```
┌─────────────────────────────────────────────────────┐
│               DEERFLOW ENFORCEMENT PIPELINE          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐    │
│  │ ANALYZE  │──▶│  PLAN    │──▶│  IMPLEMENT   │    │
│  │          │   │          │   │              │    │
│  │ • Parse  │   │ • Design │   │ • Incremental│    │
│  │ • Class  │   │ • Data   │   │ • Validate   │    │
│  │ • Risk   │   │ • File   │   │ • Test       │    │
│  └──────────┘   └──────────┘   └──────┬───────┘    │
│                                       │             │
│           ┌───────────────────────────┘             │
│           ▼                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐    │
│  │  TEST    │──▶│  VERIFY  │──▶│  VALIDATE    │    │
│  │          │   │          │   │              │    │
│  │ • Unit   │   │ • Build  │   │ • E2E        │    │
│  │ • Integ  │   │ • Sec    │   │ • A11y       │    │
│  │ • Edge   │   │ • Bundle │   │ • Responsive │    │
│  └──────────┘   └──────────┘   └──────┬───────┘    │
│                                       │             │
│           ┌───────────────────────────┘             │
│           ▼                                         │
│  ┌──────────────────────────────────────────┐       │
│  │            COMPLETE                       │       │
│  │  All 6 quality gates must PASS           │       │
│  │  Any violation = BLOCKED                  │       │
│  └──────────────────────────────────────────┘       │
│                                                      │
│  Quality Gates: Lint │ TypeCheck │ Tests │ Build     │
│                   Security │ Bundle │ A11y │ Size     │
└─────────────────────────────────────────────────────┘
```

## 🛡️ Supported AI Agents

| Agent | Config File | Status |
|-------|------------|--------|
| **Cursor IDE** | `.cursorrules` | ✅ Full support |
| **Claude Code** | `CLAUDE.md` | ✅ Full support |
| **Claude Desktop** | `CLAUDE.md` | ✅ Full support |
| **GitHub Copilot** | `.github/copilot-instructions.md` | ✅ Full support |
| **Windsurf** | `.ai/WINDSURF.md` | ✅ Full support |
| **Zed Editor** | `.ai/AGENTS.md` | ✅ Full support |
| **Amazon Q Developer** | `.ai/AGENTS.md` | ✅ Full support |
| **Tabnine** | `.ai/AGENTS.md` | ✅ Full support |
| **Codeium / Continue** | `.ai/AGENTS.md` | ✅ Full support |
| **Devin / OpenHands** | `.ai/AGENTS.md` | ✅ Full support |
| **SWE-Agent** | `.ai/AGENTS.md` | ✅ Full support |
| **AutoGPT / BabyAGI** | `.ai/SYSTEM_PROMPT.md` | ✅ Full support |
| **MetaGPT / ChatDev** | `.ai/SYSTEM_PROMPT.md` | ✅ Full support |
| **ANY custom agent** | `.ai/SYSTEM_PROMPT.md` | ✅ Full support |

## 🔧 DeerFlow CLI

```bash
# Scan project for violations
deerflow scan

# Run full enforcement pipeline
deerflow enforce

# Generate quality report
deerflow report

# Validate a task before starting
deerflow validate --task "Create a user authentication system"
```

## 🔒 Enforcement Layers

DeerFlow uses **5 layers of enforcement** to ensure compliance:

### Layer 1: AI Agent Instructions (Soft Enforcement)
- Configuration files that AI agents read at project start
- `.cursorrules`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.ai/AGENTS.md`
- Contains the 22 rules with clear explanations and examples

### Layer 2: Git Hooks (Hard Enforcement)
- `pre-commit`: 6 quality gates before any commit
- `pre-push`: 4 quality gates before any push
- Blocks: secret leaks, console.log, prohibited patterns, incomplete code

### Layer 3: CI/CD Pipeline (Automated Enforcement)
- GitHub Actions workflows run on every push/PR
- 5 quality gates + security scan
- Blocks merge on violations

### Layer 4: Python Engine (Programmatic Enforcement)
- `deerflow-core/engine/` — Python-based enforcement engine
- Prohibited pattern detection
- Build size verification
- Function complexity analysis
- Comprehensive violation reporting

### Layer 5: Context Management (Intelligent Enforcement)
- Decision tracking across sessions
- Error/solution logging
- Architecture decision records
- Checkpoint recovery for long tasks

## ⚙️ Configuration

Edit `deerflow.yaml` to customize enforcement:

```yaml
enforcement:
  level: "strict"          # strict | moderate | relaxed
  auto_fix: true           # Auto-fix linting issues
  block_on_violation: true # Block commits on violations

project:
  min_build_size_kb: 100   # Minimum build output size
  max_function_lines: 50   # Max lines per function
  test_coverage_minimum: 80 # Minimum test coverage %
  max_bundle_size_mb: 5    # Maximum JS bundle size
```

## 📊 Quality Gates

### Pre-Commit (6 gates)
1. **File Safety** — No unexpected file deletions
2. **Secret Detection** — No hardcoded passwords/keys
3. **Console.log** — No debug logging in production
4. **Prohibited Patterns** — No eval, TODO, placeholder
5. **Incomplete Code** — No TODO/FIXME/HACK markers
6. **Type Safety** — No TypeScript errors

### Pre-Push (4 gates)
1. **Test Suite** — All tests must pass
2. **Build Verification** — Build succeeds with proper size
3. **Security Audit** — No high/critical vulnerabilities
4. **Dependency Integrity** — No unmet peer dependencies

### CI/CD (5 gates)
1. **Secret Detection** — Deep scan for credentials
2. **Prohibited Patterns** — eval, dangerous APIs
3. **Console.log** — Debug statement detection
4. **Build Size** — Verify output completeness
5. **Incomplete Code** — TODO/FIXME detection

## 🧩 Agent Skill System

DeerFlow includes a **progressive skill loading system** inspired by ByteDance's architecture:

| Skill | Description | Priority |
|-------|-------------|----------|
| **coding** | Write production-ready, fully-implemented code | 1 (Critical) |
| **security** | Secure coding practices, OWASP compliance | 1 (Critical) |
| **testing** | Comprehensive testing for all code | 2 (High) |
| **architecture** | Design and implement proper architecture | 2 (High) |
| **deployment** | Prepare code for production deployment | 3 (Medium) |
| **documentation** | Write comprehensive documentation | 5 (Low) |

Each skill has:
- **Rules**: Specific coding rules to follow
- **Constraints**: Hard limits that cannot be violated
- **Required Tools**: Tools that must be available
- **Validation Checks**: Automated checks to verify compliance

## 🤝 Contributing

1. Fork this repo
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Run `bash scripts/validate.sh` — all checks must pass
4. Commit with conventional commits: `git commit -m "feat: add new rule"`
5. Push and create a Pull Request

## 📄 License

MIT License — Free for personal and commercial use.

---

## 🌟 Why DeerFlow Agent Enforcer?

In 2025-2026, AI agents have become powerful but **dangerously unreliable** without guardrails. They:
- Delete files accidentally
- Write mock code instead of real implementations
- Hallucinate API usage
- Create tiny builds with missing assets
- Skip security practices
- Lose context over long conversations

**DeerFlow Agent Enforcer solves all of these problems** with a multi-layered enforcement framework that works with ANY AI agent, in ANY project, with a single `git clone`.

> *"AI agents are powerful tools. DeerFlow makes them reliable."*

---

<p align="center">
  <strong>Built with 🦌 by the DeerFlow community</strong><br>
  <em>Inspired by <a href="https://github.com/bytedance/deer-flow">DeerFlow</a> by ByteDance</em>
</p>
