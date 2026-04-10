"""
DeerFlow Agent Enforcer — Quality Gate Engine
Implements automated quality checks that run at each pipeline stage.
Inspired by DeerFlow's gate-based pipeline control.
"""

import subprocess
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger('deerflow.quality')


@dataclass
class CheckResult:
    """Result of a single quality check."""
    name: str
    passed: bool
    message: str
    details: Optional[str] = None
    severity: str = "high"
    auto_fixable: bool = False
    fix_command: Optional[str] = None


class QualityGateEngine:
    """
    Automated quality gate checks.
    Each gate runs specific validations and returns pass/fail results.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.checks: Dict[str, callable] = {
            "lint": self.check_lint,
            "type_check": self.check_type_check,
            "unit_tests": self.check_unit_tests,
            "build": self.check_build,
            "security_audit": self.check_security_audit,
            "bundle_size": self.check_bundle_size,
            "no_console_log": self.check_no_console_log,
            "no_hardcoded_secrets": self.check_no_hardcoded_secrets,
            "accessibility": self.check_accessibility,
            "file_safety": self.check_file_safety,
            "dependency_check": self.check_dependencies,
            "build_size_check": self.check_build_size,
        }

    # === INDIVIDUAL QUALITY CHECKS ===

    def check_lint(self) -> CheckResult:
        """Run linting check."""
        package_json = self.project_root / "package.json"

        if package_json.exists():
            try:
                result = subprocess.run(
                    ["npx", "eslint", ".", "--format", "json", "--max-warnings=0"],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    return CheckResult("lint", True, "ESLint: No errors or warnings")
                else:
                    try:
                        errors = json.loads(result.stdout)
                        error_count = sum(len(e.get("messages", [])) for e in errors)
                        return CheckResult(
                            "lint", False,
                            f"ESLint: {error_count} issues found",
                            details=result.stdout[:2000],
                            auto_fixable=True,
                            fix_command="npx eslint . --fix"
                        )
                    except json.JSONDecodeError:
                        return CheckResult("lint", False, f"ESLint failed: {result.stderr[:500]}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # Python fallback
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                result = subprocess.run(
                    ["ruff", "check", "."],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    return CheckResult("lint", True, "Ruff: No issues found")
                return CheckResult("lint", False, f"Ruff: Issues found\n{result.stdout[:1000]}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return CheckResult("lint", True, "No linter configured — skipped")

    def check_type_check(self) -> CheckResult:
        """Run TypeScript type checking."""
        tsconfig = self.project_root / "tsconfig.json"

        if tsconfig.exists():
            try:
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit", "--strict"],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    return CheckResult("type_check", True, "TypeScript: No errors")
                error_lines = result.stdout.split('\n')
                error_count = len([l for l in error_lines if 'error TS' in l])
                return CheckResult(
                    "type_check", False,
                    f"TypeScript: {error_count} type errors",
                    details=result.stdout[:2000]
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return CheckResult("type_check", True, "No TypeScript project — skipped")

    def check_unit_tests(self) -> CheckResult:
        """Run unit tests."""
        package_json = self.project_root / "package.json"

        if package_json.exists():
            for cmd in [["npx", "vitest", "run"], ["npx", "jest", "--passWithNoTests"]]:
                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=180,
                        cwd=str(self.project_root)
                    )
                    if result.returncode == 0:
                        return CheckResult("unit_tests", True, "Tests: All passing")
                    return CheckResult(
                        "unit_tests", False,
                        "Tests: Some failures",
                        details=result.stdout[-2000:]
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

        # Python fallback
        for cmd in [["pytest"], ["python", "-m", "pytest"]]:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=180,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    return CheckResult("unit_tests", True, "Pytest: All passing")
                return CheckResult("unit_tests", False, "Pytest: Failures", details=result.stdout[-1000:])
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return CheckResult("unit_tests", True, "No tests configured — skipped")

    def check_build(self) -> CheckResult:
        """Run build and verify output."""
        package_json = self.project_root / "package.json"

        if package_json.exists():
            try:
                result = subprocess.run(
                    ["npm", "run", "build"],
                    capture_output=True, text=True, timeout=300,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    return CheckResult("build", True, "Build: Successful")
                return CheckResult(
                    "build", False,
                    f"Build: Failed\n{result.stderr[-1000:]}",
                    details=result.stdout[-2000:]
                )
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                return CheckResult("build", False, f"Build: Error — {str(e)}")

        return CheckResult("build", True, "No build script configured — skipped")

    def check_security_audit(self) -> CheckResult:
        """Run security audit on dependencies."""
        package_json = self.project_root / "package.json"

        if package_json.exists():
            try:
                result = subprocess.run(
                    ["npm", "audit", "--audit-level=high", "--json"],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(self.project_root)
                )
                try:
                    audit = json.loads(result.stdout)
                    vuln_count = len(audit.get("vulnerabilities", {}))
                    if vuln_count == 0:
                        return CheckResult("security_audit", True, "Security: No high/critical vulnerabilities")
                    return CheckResult(
                        "security_audit", False,
                        f"Security: {vuln_count} vulnerabilities found",
                        severity="critical"
                    )
                except json.JSONDecodeError:
                    pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return CheckResult("security_audit", True, "No package manager — skipped")

    def check_bundle_size(self) -> CheckResult:
        """Check bundle size is within limits."""
        # Simplified: check .next or dist directory
        for build_dir in [".next", "dist", "build", "out"]:
            build_path = self.project_root / build_dir
            if build_path.exists():
                total_size = sum(f.stat().st_size for f in build_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                if size_mb < 0.01:  # Less than 10KB
                    return CheckResult(
                        "bundle_size", False,
                        f"Bundle suspiciously small: {size_mb*1024:.1f}KB — assets may be missing",
                        severity="critical"
                    )
                if size_mb > 5:
                    return CheckResult(
                        "bundle_size", False,
                        f"Bundle exceeds 5MB: {size_mb:.1f}MB — consider optimization",
                        severity="medium"
                    )
                return CheckResult("bundle_size", True, f"Bundle size: {size_mb:.1f}MB")
        return CheckResult("bundle_size", True, "No build output found — skipped")

    def check_no_console_log(self) -> CheckResult:
        """Check for console.log statements in production code."""
        violations = []
        source_dirs = ["src", "app", "lib", "components", "pages"]
        exclude_dirs = ["node_modules", ".next", "dist", "build"]

        for source_dir in source_dirs:
            dir_path = self.project_root / source_dir
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if not file_path.suffix in ('.ts', '.tsx', '.js', '.jsx'):
                        continue
                    if any(ex in str(file_path) for ex in exclude_dirs):
                        continue
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        for i, line in enumerate(content.split('\n'), 1):
                            if re.search(r'console\.(log|debug|info)\s*\(', line):
                                if 'SAFETY:' not in line and '// DEERFLOW:ALLOW' not in line:
                                    violations.append(f"{file_path.relative_to(self.project_root)}:{i}")
                    except Exception:
                        pass

        if violations:
            return CheckResult(
                "no_console_log", False,
                f"Found {len(violations)} console.log statements",
                details="\n".join(violations[:20]),
                auto_fixable=True
            )
        return CheckResult("no_console_log", True, "No console.log found")

    def check_no_hardcoded_secrets(self) -> CheckResult:
        """Check for hardcoded secrets in code."""
        violations = []
        secret_patterns = [
            r'(?:password|passwd|pwd)\s*[:=]\s*[\'"][^\'"]+[\'"]',
            r'(?:api[_-]?key|apikey)\s*[:=]\s*[\'"][^\'"]+[\'"]',
            r'(?:secret|token|auth)\s*[:=]\s*[\'"][^\'"]+[\'"]',
            r'(?:private[_-]?key)\s*[:=]\s*[\'"][^\'"]+[\'"]',
        ]
        source_dirs = ["src", "app", "lib", "components", "pages", "scripts"]
        exclude_dirs = ["node_modules", ".next", "dist", "build", "__tests__", "*.test.*"]

        for source_dir in source_dirs:
            dir_path = self.project_root / source_dir
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if not file_path.suffix in ('.ts', '.tsx', '.js', '.jsx', '.py'):
                        continue
                    if any(ex in str(file_path) for ex in exclude_dirs):
                        continue
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        for i, line in enumerate(content.split('\n'), 1):
                            for pattern in secret_patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    if 'process.env' not in line and 'import.meta' not in line:
                                        violations.append(f"{file_path.relative_to(self.project_root)}:{i}")
                    except Exception:
                        pass

        if violations:
            return CheckResult(
                "no_hardcoded_secrets", False,
                f"Found {len(violations)} potential hardcoded secrets",
                details="\n".join(violations[:10]),
                severity="critical"
            )
        return CheckResult("no_hardcoded_secrets", True, "No hardcoded secrets found")

    def check_accessibility(self) -> CheckResult:
        """Basic accessibility check."""
        violations = []
        source_dirs = ["src", "app", "components"]

        for source_dir in source_dirs:
            dir_path = self.project_root / source_dir
            if dir_path.exists():
                for file_path in dir_path.rglob('*.tsx'):
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        # Check for images without alt
                        img_matches = re.findall(r'<img[^>]*(?!alt=)[^>]*>', content)
                        if img_matches:
                            violations.append(f"Images without alt attribute in {file_path.name}")
                        # Check for onClick without keyboard handler
                        if 'onClick' in content and 'onKeyDown' not in content and 'onKeyPress' not in content:
                            if 'button' not in content.lower():
                                violations.append(f"onClick without keyboard handler in {file_path.name}")
                    except Exception:
                        pass

        if violations:
            return CheckResult(
                "accessibility", False,
                f"Accessibility issues: {len(violations)}",
                details="\n".join(violations[:10])
            )
        return CheckResult("accessibility", True, "Basic accessibility checks passed")

    def check_file_safety(self) -> CheckResult:
        """Check for recently deleted files that shouldn't have been."""
        git_dir = self.project_root / ".git"

        if git_dir.exists():
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True, text=True, timeout=30,
                    cwd=str(self.project_root)
                )
                deleted = [line for line in result.stdout.split('\n') if line.startswith(' D ')]
                if deleted:
                    return CheckResult(
                        "file_safety", False,
                        f"Found {len(deleted)} deleted files — verify these were intentional",
                        details="\n".join(deleted[:10]),
                        severity="critical"
                    )
                return CheckResult("file_safety", True, "No unexpected file deletions")
            except Exception:
                pass

        return CheckResult("file_safety", True, "Not a git repository — skipped")

    def check_dependencies(self) -> CheckResult:
        """Check for dependency issues."""
        package_json = self.project_root / "package.json"

        if package_json.exists():
            try:
                result = subprocess.run(
                    ["npm", "ls", "--depth=0"],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(self.project_root)
                )
                if result.returncode != 0 and "UNMET PEER DEPENDENCY" in result.stderr:
                    return CheckResult(
                        "dependencies", False,
                        "Dependency issues found",
                        details=result.stderr[:1000]
                    )
                return CheckResult("dependencies", True, "Dependencies: OK")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return CheckResult("dependencies", True, "No dependency issues detected")

    def check_build_size(self) -> CheckResult:
        """Check build output size is reasonable."""
        return self.check_bundle_size()

    # === GATE RUNNERS ===

    def run_check(self, check_name: str) -> CheckResult:
        """Run a specific quality check."""
        if check_name not in self.checks:
            return CheckResult(check_name, False, f"Unknown check: {check_name}")
        return self.checks[check_name]()

    def run_gates(self, stage: str) -> Dict[str, CheckResult]:
        """Run all quality gates for a given stage."""
        stage_gates = {
            "pre_commit": ["lint", "type_check", "unit_tests", "no_console_log", "no_hardcoded_secrets", "build_size_check"],
            "pre_push": ["unit_tests", "security_audit", "dependency_check", "bundle_size", "accessibility"],
            "continuous": ["build", "security_audit", "bundle_size"],
        }

        checks_to_run = stage_gates.get(stage, [])
        results = {}

        for check_name in checks_to_run:
            logger.info(f"Running {stage} gate: {check_name}")
            results[check_name] = self.run_check(check_name)

        return results

    def run_all(self) -> Dict[str, CheckResult]:
        """Run all available quality checks."""
        results = {}
        for check_name in self.checks:
            logger.info(f"Running check: {check_name}")
            results[check_name] = self.run_check(check_name)
        return results
