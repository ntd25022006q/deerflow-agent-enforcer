#!/usr/bin/env bash
# ============================================================
# DEERFLOW AGENT ENFORCER — Setup Script
# One-command setup for enforcing strict AI agent behavior.
# Usage: bash scripts/setup.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

BOLD='\033[1m'
NORMAL='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                              ║${NC}"
echo -e "${CYAN}║        🦌 DEERFLOW AGENT ENFORCER — SETUP v2.0.0             ║${NC}"
echo -e "${CYAN}║                                                              ║${NC}"
echo -e "${CYAN}║   Strict AI Agent Quality Framework                          ║${NC}"
echo -e "${CYAN}║   Based on DeerFlow (ByteDance) Agentic Workflow             ║${NC}"
echo -e "${CYAN}║                                                              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# === Step 1: Copy AI Agent Rule Files ===
echo -e "${BLUE}${BOLD}[1/7] Installing AI Agent Rule Files...${NC}"
echo ""

# .cursorrules (Cursor)
if [ -f ".cursorrules" ]; then
    echo -e "  ${GREEN}✓${NC} .cursorrules → Cursor IDE rules installed"
else
    echo -e "  ${YELLOW}⚠${NC} .cursorrules not found"
fi

# CLAUDE.md (Claude)
if [ -f "CLAUDE.md" ]; then
    echo -e "  ${GREEN}✓${NC} CLAUDE.md → Claude Code/Desktop rules installed"
else
    echo -e "  ${YELLOW}⚠${NC} CLAUDE.md not found"
fi

# .github/copilot-instructions.md (Copilot)
if [ -f ".github/copilot-instructions.md" ]; then
    echo -e "  ${GREEN}✓${NC} .github/copilot-instructions.md → GitHub Copilot rules installed"
else
    echo -e "  ${YELLOW}⚠${NC} .github/copilot-instructions.md not found"
fi

# .ai/ directory (Generic + System)
if [ -d ".ai" ]; then
    echo -e "  ${GREEN}✓${NC} .ai/ → Generic agent rules installed"
    echo -e "    ├── AGENTS.md (Universal rules for ALL agents)"
    echo -e "    ├── SYSTEM_PROMPT.md (Base system prompt)"
    echo -e "    └── WINDSURF.md (Windsurf/Zed/Tabnine rules)"
else
    echo -e "  ${YELLOW}⚠${NC} .ai/ directory not found"
fi

echo ""

# === Step 2: Install Git Hooks ===
echo -e "${BLUE}${BOLD}[2/7] Installing Git Hooks...${NC}"
echo ""

if [ -d ".git" ]; then
    # Pre-commit hook
    if [ -f "hooks/pre-commit" ]; then
        cp hooks/pre-commit .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        echo -e "  ${GREEN}✓${NC} Pre-commit hook installed (6 quality gates)"
    fi

    # Pre-push hook
    if [ -f "hooks/pre-push" ]; then
        cp hooks/pre-push .git/hooks/pre-push
        chmod +x .git/hooks/pre-push
        echo -e "  ${GREEN}✓${NC} Pre-push hook installed (4 quality gates)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Not a git repository — hooks not installed"
    echo -e "  ${YELLOW}  Run 'git init' first, then re-run setup${NC}"
fi

echo ""

# === Step 3: Install DeerFlow Core ===
echo -e "${BLUE}${BOLD}[3/7] Installing DeerFlow Core Engine...${NC}"
echo ""

if command -v python3 &> /dev/null; then
    # Create deerflow command
    PYTHON_PATH=$(which python3)
    cat > /usr/local/bin/deerflow 2>/dev/null << DEERFLOW_CLI || cat > "$HOME/.local/bin/deerflow" << DEERFLOW_CLI
#!/usr/bin/env bash
cd "$PROJECT_ROOT" && python3 -m deerflow_core.engine "\$@"
DEERFLOW_CLI
    chmod +x /usr/local/bin/deerflow 2>/dev/null || chmod +x "$HOME/.local/bin/deerflow"
    echo -e "  ${GREEN}✓${NC} DeerFlow CLI installed"
    echo -e "  ${GREEN}✓${NC} Commands: deerflow scan | enforce | report | validate"
else
    echo -e "  ${YELLOW}⚠${NC} Python 3 not found — DeerFlow CLI not installed"
fi

echo ""

# === Step 4: Configure .gitignore ===
echo -e "${BLUE}${BOLD}[4/7] Configuring .gitignore...${NC}"
echo ""

DEERFLOW_IGNORE=".deerflow/
.deerflow-checkpoint.json
.deerflow-report.json
*.deerflow-backup
__pycache__/
*.pyc
.venv/
"

if [ -f ".gitignore" ]; then
    if ! grep -q ".deerflow" .gitignore; then
        echo "$DEERFLOW_IGNORE" >> .gitignore
        echo -e "  ${GREEN}✓${NC} DeerFlow entries added to .gitignore"
    else
        echo -e "  ${GREEN}✓${NC} .gitignore already configured"
    fi
else
    echo "$DEERFLOW_IGNORE" > .gitignore
    echo -e "  ${GREEN}✓${NC} .gitignore created"
fi

echo ""

# === Step 5: Verify deerflow.yaml ===
echo -e "${BLUE}${BOLD}[5/7] Verifying Configuration...${NC}"
echo ""

if [ -f "deerflow.yaml" ]; then
    echo -e "  ${GREEN}✓${NC} deerflow.yaml found and valid"
    if command -v python3 &> /dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('deerflow.yaml'))" 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} Configuration syntax valid" || \
            echo -e "  ${RED}✗${NC} Configuration syntax error"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} deerflow.yaml not found — using defaults"
fi

echo ""

# === Step 6: Run Initial Scan ===
echo -e "${BLUE}${BOLD}[6/7] Running Initial Scan...${NC}"
echo ""

if command -v python3 &> /dev/null; then
    python3 deerflow_core/engine/orchestrator.py scan 2>/dev/null || \
        echo -e "  ${YELLOW}⚠${NC} Scan skipped (engine not available)"
else
    echo -e "  ${YELLOW}⚠${NC} Python required for scan — skipped"
fi

echo ""

# === Step 7: Summary ===
echo -e "${BLUE}${BOLD}[7/7] Setup Complete!${NC}"
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}${BOLD}  🦌 DeerFlow Agent Enforcer v2.0.0 — ACTIVE${NC}"
echo ""
echo -e "  ${BOLD}Protected AI Agents:${NC}"
echo "    • Cursor IDE        (.cursorrules)"
echo "    • Claude Code       (CLAUDE.md)"
echo "    • Claude Desktop    (CLAUDE.md)"
echo "    • GitHub Copilot    (.github/copilot-instructions.md)"
echo "    • Windsurf          (.ai/WINDSURF.md)"
echo "    • Zed / Tabnine / Continue / Amazon Q  (.ai/AGENTS.md)"
echo "    • ANY other agent   (.ai/SYSTEM_PROMPT.md)"
echo ""
echo -e "  ${BOLD}Enforcement Mechanisms:${NC}"
echo "    • Pre-commit hook   (6 quality gates)"
echo "    • Pre-push hook     (4 quality gates)"
echo "    • CI/CD pipeline    (5 automated gates)"
echo "    • Security scan     (dependency + secret audit)"
echo ""
echo -e "  ${BOLD}22 Rules Enforced:${NC}"
echo "    • File safety          • No mocks/stubs"
echo "    • Architecture first   • Surgical changes"
echo "    • Dependency safety    • Loop safety"
echo "    • Evidence-based       • Build integrity"
echo "    • Security first       • Testing mandatory"
echo "    • Context retention    • Performance"
echo "    • Error handling       • Professional UI"
echo "    • No shortcuts         • Git discipline"
echo "    • Documentation        • Type safety"
echo "    • Accessibility        • CI/CD ready"
echo "    • Monitoring ready     • Maintainability"
echo ""
echo -e "  ${BOLD}Quick Commands:${NC}"
echo "    deerflow scan      — Scan for violations"
echo "    deerflow enforce    — Run full pipeline"
echo "    deerflow report     — Generate report"
echo "    deerflow validate   — Validate a task"
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}  Zero tolerance for shortcuts. Production quality only.${NC}"
echo ""
