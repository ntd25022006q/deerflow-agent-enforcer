# 🧩 DeerFlow Agent Enforcer — Skill System

## Overview

The DeerFlow Skill System is inspired by ByteDance's DeerFlow architecture, which uses **progressive skill loading** — agents only load the capabilities they need, when they need them. This prevents context bloat and ensures focused, high-quality output.

## Skill Architecture

```
┌─────────────────────────────────────────────────┐
│              SKILL REGISTRY                      │
│                                                  │
│  ┌───────────┐ ┌───────────┐ ┌──────────────┐  │
│  │  CODING   │ │ SECURITY  │ │   TESTING    │  │
│  │ Priority:1│ │ Priority:1│ │  Priority:2  │  │
│  └───────────┘ └───────────┘ └──────────────┘  │
│                                                  │
│  ┌───────────┐ ┌───────────┐ ┌──────────────┐  │
│  │   ARCH    │ │   DEPLOY  │ │     DOCS     │  │
│  │ Priority:2│ │ Priority:3│ │  Priority:5  │  │
│  └───────────┘ └───────────┘ └──────────────┘  │
│                                                  │
│  Each skill has:                                 │
│  • Rules (what to follow)                        │
│  • Constraints (what NOT to do)                  │
│  • Required Tools (what must be available)       │
│  • Validation Checks (automated verification)    │
└─────────────────────────────────────────────────┘
```

## Built-in Skills

### 1. Coding (Priority: 1 — Critical)

**When activated**: Every coding task

**Rules**:
- Follow project conventions
- Strict typing (no `any` without justification)
- No prohibited patterns
- Comprehensive error handling
- Complete implementation (no stubs)
- No infinite loops
- Proper async handling
- Clean code principles

**Constraints**:
- NO mock data in production code
- NO TODO comments
- NO `any` type without justification
- Functions must be < 50 lines
- Cyclomatic complexity < 10

**Validation Checks**:
- All functions implemented
- No prohibited patterns detected
- Type safety verified
- Error handling complete

### 2. Security (Priority: 1 — Critical)

**When activated**: Every task involving user input, auth, or data handling

**Rules**:
- No hardcoded secrets
- Input validation required
- XSS prevention
- CSRF protection
- SQL injection prevention
- Dependency audit
- Secure headers (CSP, CORS, HSTS)

**Constraints**:
- ALL secrets in environment variables
- Parameterized queries ONLY for SQL
- Sanitize ALL user-provided content
- NO `eval()`, NO `innerHTML` with user data

**Validation Checks**:
- No secrets in code
- Input validation present
- Security headers configured
- Dependency audit clean

### 3. Testing (Priority: 2 — High)

**When activated**: After implementing any feature

**Rules**:
- Unit tests for all functions
- Integration tests for APIs
- E2E tests for critical paths
- Edge case coverage
- No skipped tests
- Meaningful assertions

**Constraints**:
- Every new function MUST have at least 1 test
- Every component MUST have render test
- Edge cases: null, empty, large, concurrent
- Test names describe expected behavior

**Validation Checks**:
- Coverage threshold met (≥80%)
- All tests passing
- No skipped tests
- Edge cases covered

### 4. Architecture (Priority: 2 — High)

**When activated**: Before starting any new feature or major change

**Rules**:
- Plan before code
- Component hierarchy
- State management strategy
- Proper file structure
- Separation of concerns
- Dependency inversion

**Constraints**:
- Design before implementation
- Document architecture decisions (ADR)
- Follow existing project patterns
- Single responsibility per module

**Validation Checks**:
- Architecture documented
- Components properly separated
- Dependencies managed
- File structure consistent

### 5. Deployment (Priority: 3 — Medium)

**When activated**: When preparing for production

**Rules**:
- Build verification
- Env vars only for secrets
- CI/CD pipeline passes
- Monitoring ready
- Rollback strategy

**Constraints**:
- Build must include all assets
- Environment variables for ALL config
- Health check endpoints
- Graceful shutdown handling

**Validation Checks**:
- Build complete
- Environment variables configured
- CI/CD passes
- Monitoring setup

### 6. Documentation (Priority: 5 — Low)

**When activated**: After implementation is complete

**Rules**:
- Inline comments for complexity
- JSDoc for public APIs
- ADR for decisions
- README updated
- Changelog maintained

**Constraints**:
- Complex logic: explain WHY, not WHAT
- Public APIs: complete JSDoc/docstrings
- Architecture changes: create ADR

**Validation Checks**:
- Public APIs documented
- Complex logic commented
- README complete

## Skill Activation

Skills are activated based on the current task phase:

```
Task Start → ACTIVATE: coding, architecture
            → Design phase → architecture rules active
            → Implement phase → coding rules active
            → After code → ACTIVATE: testing
            → After tests → ACTIVATE: security
            → Before deploy → ACTIVATE: deployment
            → Final → ACTIVATE: documentation
```

## Custom Skills

You can add custom skills by creating YAML files in `deerflow-core/skills/`:

```yaml
name: my_custom_skill
version: "1.0.0"
description: "My custom enforcement skill"
category: custom
rules:
  - rule_one
  - rule_two
constraints:
  - "Constraint description"
validation_checks:
  - check_one
priority: 3
enabled: true
```

Custom skills are automatically loaded by the Skill Registry at startup.
