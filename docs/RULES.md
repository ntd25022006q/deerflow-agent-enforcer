# 📏 DeerFlow Agent Enforcer — Complete Rules Reference

## The 22 Rules

### Category 1: Safety (Violation = Immediate Stop)

#### R01 — FILE PRESERVATION
- **Severity**: Critical
- **Action**: Block
- **Rule**: NEVER delete any file without explicit user confirmation + git backup
- **Enforcement**: Pre-commit hook, pre-push hook, CI/CD
- **How to comply**: Use `git status` before/after file operations, create backups, ask user

#### R02 — DEPENDENCY INTEGRITY
- **Severity**: Critical
- **Action**: Block
- **Rule**: Check compatibility before installing any package
- **Enforcement**: Pre-push hook, quality gate engine
- **How to comply**: Run `npm ls`, `pip check` before installing, verify version ranges

#### R03 — BUILD VERIFICATION
- **Severity**: Critical
- **Action**: Block
- **Rule**: Build output must meet minimum size requirements
- **Enforcement**: Pre-push hook, CI/CD, build size check
- **How to comply**: Verify build includes all assets, check output directory

#### R04 — SECURITY ABSOLUTES
- **Severity**: Critical
- **Action**: Block
- **Rule**: No secrets in code, input validation, XSS/CSRF prevention
- **Enforcement**: Secret detection in pre-commit, CI/CD security scan
- **How to comply**: Use env vars, parameterized queries, sanitize inputs

### Category 2: Quality (Violation = Must Fix)

#### R05 — NO PLACEHOLDER CODE
- **Severity**: Critical
- **Action**: Block
- **Rule**: Every function fully implemented, no TODOs/stubs/mocks
- **Enforcement**: Prohibited pattern detection, incomplete code gate
- **How to comply**: Implement everything, or say "I can't complete X"

#### R06 — ARCHITECTURE FIRST
- **Severity**: High
- **Action**: Warn
- **Rule**: Plan architecture before writing any code
- **Enforcement**: AI agent instructions (Layer 1)
- **How to comply**: Create plan, get alignment, then code

#### R07 — INCREMENTAL CHANGES
- **Severity**: High
- **Action**: Warn
- **Rule**: Read existing code, change minimally, preserve patterns
- **Enforcement**: AI agent instructions (Layer 1)
- **How to comply**: Read file first, understand it, make targeted changes

#### R08 — LOOP & STATE SAFETY
- **Severity**: Critical
- **Action**: Block
- **Rule**: All loops terminate, all async has timeout, all recursion has base case
- **Enforcement**: AI agent instructions, code review
- **How to comply**: Add exit conditions, timeouts, base cases

#### R09 — EVIDENCE-BASED API USAGE
- **Severity**: High
- **Action**: Warn
- **Rule**: Verify APIs against official docs, never hallucinate
- **Enforcement**: AI agent instructions
- **How to comply**: Use web search, cite documentation URLs

#### R10 — COMPREHENSIVE ERROR HANDLING
- **Severity**: High
- **Action**: Warn
- **Rule**: try/catch on all async, graceful failures, meaningful messages
- **Enforcement**: Code review, quality gates
- **How to comply**: Wrap async operations, handle all error states

#### R11 — MANDATORY TESTING
- **Severity**: High
- **Action**: Block
- **Rule**: Test every function, component, and endpoint
- **Enforcement**: Pre-push hook requires tests to pass
- **How to comply**: Write tests alongside code, cover edge cases

#### R12 — TYPE SAFETY
- **Severity**: High
- **Action**: Block (if strict mode)
- **Rule**: Strict TypeScript, no `any` without justification
- **Enforcement**: Pre-commit type check, CI/CD
- **How to comply**: Enable strict mode, use proper types and generics

### Category 3: Performance

#### R13 — EFFICIENT RENDERING
- **Severity**: Medium
- **Action**: Warn
- **Rule**: Use React.memo, useMemo, virtualization, lazy loading
- **Enforcement**: Code review, bundle analysis
- **How to comply**: Optimize renders, lazy load routes, virtualize lists

#### R14 — BUNDLE OPTIMIZATION
- **Severity**: Medium
- **Action**: Warn
- **Rule**: Tree-shake, code-split, compress assets
- **Enforcement**: Bundle size gate in pre-push
- **How to comply**: Use dynamic imports, analyze bundle, optimize images

### Category 4: UX

#### R15 — RESPONSIVE DESIGN
- **Severity**: Medium
- **Action**: Warn
- **Rule**: Mobile-first, test at 375/768/1024/1440px
- **Enforcement**: Code review, accessibility gate
- **How to comply**: Use flexbox/grid, test breakpoints, flexible layouts

#### R16 — ACCESSIBILITY
- **Severity**: Medium
- **Action**: Warn
- **Rule**: ARIA labels, keyboard nav, WCAG AA contrast
- **Enforcement**: Accessibility gate in CI/CD
- **How to comply**: Use semantic HTML, test keyboard navigation

#### R17 — LOADING & ERROR STATES
- **Severity**: Medium
- **Action**: Warn
- **Rule**: Skeleton screens, spinners, empty states, error states
- **Enforcement**: Code review
- **How to comply**: Implement all UI states for every component

### Category 5: Process

#### R18 — CONTEXT MANAGEMENT
- **Severity**: Medium
- **Action**: Info
- **Rule**: Read project files, maintain mental model, summarize decisions
- **Enforcement**: Context manager engine
- **How to comply**: Use DeerFlow context system, track decisions

#### R19 — GIT DISCIPLINE
- **Severity**: Medium
- **Action**: Warn
- **Rule**: Meaningful commits, no secrets, proper .gitignore
- **Enforcement**: Pre-commit hook, security scan
- **How to comply**: Conventional commits, gitignore patterns

#### R20 — DOCUMENTATION
- **Severity**: Low
- **Action**: Info
- **Rule**: Inline comments for complexity, JSDoc for public APIs
- **Enforcement**: Code review
- **How to comply**: Document WHY not WHAT, ADRs for decisions

#### R21 — VERIFICATION BEFORE COMPLETION
- **Severity**: High
- **Action**: Block
- **Rule**: All checks pass before declaring "done"
- **Enforcement**: Pipeline orchestrator
- **How to comply**: Run full checklist, verify all gates

#### R22 — NO SHORTCUTS
- **Severity**: High
- **Action**: Block
- **Rule**: Zero tolerance for cutting corners
- **Enforcement**: All layers
- **How to comply**: Follow every rule, every time

## Prohibited Patterns

| Pattern | Severity | Rule |
|---------|----------|------|
| `// TODO` | High | R05 |
| `placeholder`/`dummy` data | Critical | R05 |
| `any` type (unjustified) | High | R12 |
| `eval()` | Critical | R04 |
| `innerHTML` with user data | Critical | R04 |
| Hardcoded secrets | Critical | R04 |
| `console.log` in production | Medium | R10 |
| Unhandled promise | High | R10 |
| Infinite loops | Critical | R08 |
| `@ts-ignore` (unjustified) | High | R12 |
| Deleted files without backup | Critical | R01 |
| Build < 10KB for web | Critical | R03 |
