#!/usr/bin/env bash
# ============================================================
# DEERFLOW AGENT ENFORCER — Validation Script
# Run: bash scripts/validate.sh
# Checks all aspects of the DeerFlow setup and project health.
# ============================================================

set -euo pipefail

echo "🦌 DeerFlow Agent Enforcer — Validation Report"
echo "================================================"
echo ""

ERRORS=0
WARNINGS=0
CHECKS=0

check() {
    local name="$1"
    local condition="$2"
    local level="${3:-error}"
    CHECKS=$((CHECKS + 1))

    if eval "$condition"; then
        echo "  ✅ $name"
    else
        if [ "$level" = "error" ]; then
            echo "  ❌ $name"
            ERRORS=$((ERRORS + 1))
        else
            echo "  ⚠️  $name"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# === AI Agent Configuration ===
echo "📋 AI Agent Configuration"
echo "--------------------------"
check ".cursorrules exists" "[ -f .cursorrules ]"
check "CLAUDE.md exists" "[ -f CLAUDE.md ]"
check "Copilot instructions exist" "[ -f .github/copilot-instructions.md ]"
check "Generic agent rules exist" "[ -f .ai/AGENTS.md ]"
check "System prompt exists" "[ -f .ai/SYSTEM_PROMPT.md ]"
check "Windsurf rules exist" "[ -f .ai/WINDSURF.md ]"
echo ""

# === DeerFlow Core ===
echo "🧠 DeerFlow Core Engine"
echo "-----------------------"
check "deerflow.yaml exists" "[ -f deerflow.yaml ]"
check "Orchestrator exists" "[ -f deerflow_core/engine/orchestrator.py ]"
check "Skill registry exists" "[ -f deerflow_core/engine/skill_registry.py ]"
check "Quality gate exists" "[ -f deerflow_core/engine/quality_gate.py ]"
check "Context manager exists" "[ -f deerflow_core/engine/context_manager.py ]"
echo ""

# === Git Hooks ===
echo "🪝 Git Hooks"
echo "-------------"
if [ -d ".git" ]; then
    check "Pre-commit hook installed" "[ -f .git/hooks/pre-commit ]"
    check "Pre-push hook installed" "[ -f .git/hooks/pre-push ]"
    check "Pre-commit is executable" "[ -x .git/hooks/pre-commit ]" "warning"
    check "Pre-push is executable" "[ -x .git/hooks/pre-push ]" "warning"
else
    echo "  ⚠️  Not a git repository"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# === CI/CD ===
echo "🔄 CI/CD Pipeline"
echo "-----------------"
check "Quality gate workflow exists" "[ -f .github/workflows/deerflow-quality-gate.yml ]"
check "Security scan workflow exists" "[ -f .github/workflows/deerflow-security-scan.yml ]"
echo ""

# === Project Health ===
echo "🏥 Project Health"
echo "-----------------"
check ".gitignore exists" "[ -f .gitignore ]"
check ".env not in repo" "[ ! -f .env ] || ! grep -q 'password\|secret' .env 2>/dev/null" "warning"
check "No .env in tracking" "! git ls-files .env 2>/dev/null | grep -q .env" "warning"
check "package.json or pyproject.toml exists" "[ -f package.json ] || [ -f pyproject.toml ]" "warning"
check "tsconfig.json exists (if TS project)" "[ ! -f '*.ts' ] || [ -f tsconfig.json ]" "warning"
echo ""

# === Security ===
echo "🔒 Security"
echo "-----------"
check "No hardcoded secrets in src/" "! grep -rEI '(password|secret|api_key|private_key)\s*[:=]\s*[\x27\x22]' --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' src/ 2>/dev/null" "warning"
check "No eval() in src/" "! grep -r 'eval(' --include='*.ts' --include='*.tsx' --include='*.js' src/ 2>/dev/null" "warning"
check ".env files in .gitignore" "grep -q '.env' .gitignore 2>/dev/null" "warning"
echo ""

# === Summary ===
echo "================================================"
echo "  Total checks: $CHECKS"
echo -e "  Errors: $ERRORS"
echo -e "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ All critical checks passed! DeerFlow is properly configured."
    exit 0
else
    echo "❌ $ERRORS critical issues found. Fix them before proceeding."
    exit 1
fi
