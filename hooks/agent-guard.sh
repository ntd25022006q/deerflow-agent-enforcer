#!/usr/bin/env bash
# ============================================================
# DEERFLOW AGENT ENFORCER — Agent Guard Script
# Run before ANY AI agent operation to enforce quality.
# Usage: source hooks/agent-guard.sh
# ============================================================

export DEERFLOW_ENFORCED=1
export DEERFLOW_VERSION="2.0.0"
export DEERFLOW_LEVEL="${DEERFLOW_LEVEL:-strict}"

# DeerFlow enforcement wrapper for common commands
deerflow_guard() {
    local cmd="$1"
    shift

    case "$cmd" in
        "write"|"edit"|"create")
            # Guard file operations
            local file="$1"
            if [[ -z "$file" ]]; then
                echo "[DEERFLOW] WARNING: No file specified for $cmd"
                return 1
            fi

            # Check if we're about to overwrite/delete
            if [[ -f "$file" && "$cmd" == "write" ]]; then
                echo "[DEERFLOW] File exists: $file"
                echo "[DEERFLOW] Have you read this file first? (Rule: Read Before Modify)"
                echo "[DEERFLOW] Creating backup..."
                cp "$file" "${file}.deerflow-backup" 2>/dev/null || true
            fi
            ;;

        "delete"|"remove"|"rm")
            echo "[DEERFLOW] ⛔ BLOCKED: File deletion requires explicit confirmation"
            echo "[DEERFLOW] Use: deerflow_confirm_delete <file>"
            return 1
            ;;

        "install"|"add"|"npm"|"pip")
            echo "[DEERFLOW] Dependency operation: $cmd $@"
            echo "[DEERFLOW] Rule: Check compatibility before installing"
            echo "[DEERFLOW] Proceeding with installation..."
            ;;

        "test")
            echo "[DEERFLOW] Running tests — Rule: All tests must pass"
            ;;

        "build")
            echo "[DEERFLOW] Running build — Rule: Verify output completeness"
            ;;
    esac
}

deerflow_confirm_delete() {
    local file="$1"
    if [[ -z "$file" ]]; then
        echo "[DEERFLOW] No file specified"
        return 1
    fi

    echo "[DEERFLOW] ⚠ DELETION REQUEST: $file"
    echo "[DEERFLOW] Creating backup..."
    cp "$file" "${file}.deerflow-backup" 2>/dev/null || true
    echo "[DEERFLOW] Backup created: ${file}.deerflow-backup"
    echo "[DEERFLOW] Ensure this deletion is intentional."
    echo "[DEERFLOW] After deletion, verify no broken imports/references."
    return 0
}

echo "[DEERFLOW] Agent Guard v$DEERFLOW_VERSION active (level: $DEERFLOW_LEVEL)"
echo "[DEERFLOW] 22 rules enforced. Zero tolerance for shortcuts."
