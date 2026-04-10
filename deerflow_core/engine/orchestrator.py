"""
DeerFlow Agent Enforcer — Core Engine
Version: 2.0.0
Based on ByteDance's DeerFlow architecture: Lead Agent → Sub-Agents → Sandboxed Execution

This module provides the orchestration engine that enforces strict AI agent behavior
through quality gates, skill management, and pipeline control.
"""

import os
import re
import sys
import yaml
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [DEERFLOW] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('deerflow')


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ActionType(Enum):
    BLOCK = "block"
    WARN = "warn"
    INFO = "info"


@dataclass
class Violation:
    """Represents a rule violation detected during enforcement."""
    rule_id: str
    severity: Severity
    message: str
    action: ActionType
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    context: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "action": self.action.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "context": self.context,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class QualityGateResult:
    """Result of a quality gate check."""
    gate_name: str
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "metrics": self.metrics,
            "duration_ms": self.duration_ms
        }


class DeerFlowConfig:
    """Loads and manages DeerFlow configuration from deerflow.yaml."""

    def __init__(self, config_path: str = "deerflow.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.version = self.config.get("version", "1.0.0")
        self.enforcement_level = self.config.get("enforcement", {}).get("level", "strict")

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return self._default_config()
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "version": "2.0.0",
            "enforcement": {"level": "strict", "block_on_violation": True},
            "rules": {},
            "quality_gates": {"pre_commit": [], "pre_push": [], "continuous": []}
        }

    def get_rule(self, rule_id: str) -> Optional[dict]:
        """Get a specific rule configuration."""
        return self.config.get("rules", {}).get(rule_id)

    def get_quality_gates(self, stage: str) -> List[str]:
        """Get quality gates for a specific stage."""
        return self.config.get("quality_gates", {}).get(stage, [])

    def get_project_setting(self, key: str, default: Any = None) -> Any:
        """Get a project setting."""
        return self.config.get("project", {}).get(key, default)

    def get_skill_rules(self, skill_name: str) -> List[str]:
        """Get rules for a specific skill."""
        skills = self.config.get("skills", {}).get("enabled", [])
        skill_config = self.config.get("skills", {}).get(skill_name, {})
        return skill_config.get("rules", []) if skill_name in skills else []


class RuleEngine:
    """
    Evaluates code against DeerFlow rules.
    Checks for prohibited patterns, enforces quality standards,
    and detects common AI agent mistakes.
    """

    PROHIBITED_PATTERNS = [
        ("todo_comment", r"//\s*TODO\b", Severity.HIGH, "TODO comment found — implement fully"),
        ("placeholder", r"(placeholder|dummy|fake|mock)\s*(data|value|function)", Severity.CRITICAL, "Placeholder/mock data detected"),
        ("eval_usage", r"\beval\s*\(", Severity.CRITICAL, "eval() detected — security vulnerability"),
        ("any_type", r":\s*any\b(?!\s*//\s*SAFETY)", Severity.HIGH, "Unjustified 'any' type detected"),
        ("ts_ignore", r"@ts-ignore(?!\s*//\s*reason)", Severity.HIGH, "@ts-ignore without justification"),
        ("console_log", r"console\.(log|debug|info)\s*\(", Severity.MEDIUM, "console.log in code"),
        ("hardcoded_secret", r"(password|secret|api_key|private_key)\s*[:=]\s*['\"]", Severity.CRITICAL, "Possible hardcoded secret"),
        ("dangerously_set_inner_html", r"dangerouslySetInnerHTML", Severity.HIGH, "dangerouslySetInnerHTML without sanitization"),
        ("eslint_disable", r"eslint-disable(?!\s*//\s*reason)", Severity.MEDIUM, "eslint-disable without justification"),
        ("incomplete_function", r"(\/\/\s*implement|\/\/\s*fill|\/\/\s*stub)", Severity.CRITICAL, "Incomplete function detected"),
    ]

    def __init__(self, config: DeerFlowConfig):
        self.config = config
        self.violations: List[Violation] = []

    def check_file(self, file_path: str) -> List[Violation]:
        """Check a single file for violations."""
        violations = []
        path = Path(file_path)

        if not path.exists():
            return violations

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern_id, pattern, severity, message in self.PROHIBITED_PATTERNS:
                    if self._matches_pattern(line, pattern):
                        violations.append(Violation(
                            rule_id=pattern_id,
                            severity=severity,
                            message=message,
                            action=self._get_action(severity),
                            file_path=str(file_path),
                            line_number=line_num,
                            context=line.strip()
                        ))
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")

        return violations

    def check_build_size(self, build_dir: str) -> List[Violation]:
        """Check if build output meets minimum size requirements."""
        violations = []
        min_size_kb = self.config.get_project_setting("min_build_size_kb", 100)
        build_path = Path(build_dir)

        if not build_path.exists():
            violations.append(Violation(
                rule_id="build_missing",
                severity=Severity.CRITICAL,
                message=f"Build directory not found: {build_dir}",
                action=ActionType.BLOCK
            ))
            return violations

        total_size = sum(f.stat().st_size for f in build_path.rglob('*') if f.is_file())
        size_kb = total_size / 1024

        if size_kb < min_size_kb:
            violations.append(Violation(
                rule_id="build_too_small",
                severity=Severity.CRITICAL,
                message=f"Build size {size_kb:.1f}KB is below minimum {min_size_kb}KB — assets may be missing",
                action=ActionType.BLOCK,
                metrics={"actual_kb": size_kb, "minimum_kb": min_size_kb}
            ))

        return violations

    def check_function_complexity(self, file_path: str) -> List[Violation]:
        """Check function complexity (simplified cyclomatic complexity)."""
        violations = []
        max_complexity = self.config.get_project_setting("max_complexity", 10)
        max_lines = self.config.get_project_setting("max_function_lines", 50)
        path = Path(file_path)

        if not path.exists() or path.suffix not in ('.ts', '.tsx', '.js', '.jsx', '.py'):
            return violations

        try:
            content = path.read_text(encoding='utf-8')
            current_function_start = None
            func_name = "unknown"

            for line_num, line in enumerate(content.split('\n'), 1):
                stripped = line.strip()
                func_match = re.match(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=|(?:def)\s+(\w+))', stripped)
                if func_match:
                    if current_function_start is not None:
                        func_length = line_num - current_function_start
                        if func_length > max_lines:
                            violations.append(Violation(
                                rule_id="function_too_long",
                                severity=Severity.MEDIUM,
                                message=f"Function '{func_name}' is {func_length} lines (max {max_lines})",
                                action=ActionType.WARN,
                                file_path=str(file_path),
                                line_number=current_function_start
                            ))
                    func_name = func_match.group(1) or func_match.group(2) or func_match.group(3) or "unknown"
                    current_function_start = line_num

        except Exception as e:
            logger.error(f"Error checking complexity: {e}")

        return violations

    def _matches_pattern(self, line: str, pattern: str) -> bool:
        """Check if a line matches a pattern."""
        return bool(re.search(pattern, line, re.IGNORECASE))

    def _get_action(self, severity: Severity) -> ActionType:
        """Get action type based on severity."""
        if severity in (Severity.CRITICAL, Severity.HIGH):
            return ActionType.BLOCK
        elif severity == Severity.MEDIUM:
            return ActionType.WARN
        return ActionType.INFO


class PipelineOrchestrator:
    """
    Orchestrates the DeerFlow enforcement pipeline.
    Manages workflow stages and quality gates.
    """

    STAGES = [
        "analyze", "plan", "implement", "test",
        "verify", "validate", "complete"
    ]

    def __init__(self, config: DeerFlowConfig):
        self.config = config
        self.rule_engine = RuleEngine(config)
        self.current_stage = 0
        self.results: Dict[str, QualityGateResult] = {}
        self.context: Dict[str, Any] = {}
        self.checkpoint_file = Path(".deerflow-checkpoint.json")

    def get_current_stage(self) -> str:
        """Get the name of the current pipeline stage."""
        return self.STAGES[self.current_stage] if self.current_stage < len(self.STAGES) else "done"

    def advance_stage(self) -> str:
        """Advance to the next pipeline stage."""
        if self.current_stage < len(self.STAGES) - 1:
            self.current_stage += 1
            self._save_checkpoint()
            logger.info(f"Advanced to stage: {self.get_current_stage()}")
            return self.get_current_stage()
        return "complete"

    def run_quality_gate(self, gate_name: str, check_fn: Callable) -> QualityGateResult:
        """Run a quality gate check."""
        import time
        start = time.time()
        logger.info(f"Running quality gate: {gate_name}")

        try:
            passed, violations, metrics = check_fn()
            result = QualityGateResult(
                gate_name=gate_name,
                passed=passed,
                violations=violations,
                metrics=metrics or {},
                duration_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            result = QualityGateResult(
                gate_name=gate_name,
                passed=False,
                violations=[Violation(
                    rule_id="gate_error",
                    severity=Severity.CRITICAL,
                    message=f"Quality gate '{gate_name}' failed with error: {str(e)}",
                    action=ActionType.BLOCK
                )],
                duration_ms=int((time.time() - start) * 1000)
            )

        self.results[gate_name] = result
        self._save_checkpoint()

        if not result.passed:
            logger.error(f"Quality gate FAILED: {gate_name}")
            for v in result.violations:
                logger.error(f"  - [{v.severity.value}] {v.message} ({v.file_path}:{v.line_number})")
        else:
            logger.info(f"Quality gate PASSED: {gate_name}")

        return result

    def can_proceed(self) -> bool:
        """Check if the pipeline can proceed (all gates passed)."""
        return all(r.passed for r in self.results.values())

    def get_report(self) -> dict:
        """Generate a comprehensive enforcement report."""
        total_violations = sum(len(r.violations) for r in self.results.values())
        failed_gates = [name for name, r in self.results.items() if not r.passed]
        passed_gates = [name for name, r in self.results.items() if r.passed]

        return {
            "timestamp": datetime.now().isoformat(),
            "version": self.config.version,
            "enforcement_level": self.config.enforcement_level,
            "current_stage": self.get_current_stage(),
            "summary": {
                "total_gates": len(self.results),
                "passed": len(passed_gates),
                "failed": len(failed_gates),
                "total_violations": total_violations,
                "can_proceed": self.can_proceed()
            },
            "gates": {name: r.to_dict() for name, r in self.results.items()},
            "failed_gate_names": failed_gates,
            "passed_gate_names": passed_gates
        }

    def _save_checkpoint(self):
        """Save pipeline state for recovery."""
        try:
            data = {
                "current_stage": self.current_stage,
                "results": {name: r.to_dict() for name, r in self.results.items()},
                "context": self.context,
                "timestamp": datetime.now().isoformat()
            }
            self.checkpoint_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not save checkpoint: {e}")

    def load_checkpoint(self) -> bool:
        """Load pipeline state from checkpoint."""
        if not self.checkpoint_file.exists():
            return False
        try:
            data = json.loads(self.checkpoint_file.read_text(encoding='utf-8'))
            self.current_stage = data.get("current_stage", 0)
            self.context = data.get("context", {})
            for name, result_data in data.get("results", {}).items():
                violations = [
                    Violation(
                        rule_id=v["rule_id"],
                        severity=Severity(v["severity"]),
                        message=v["message"],
                        action=ActionType(v["action"]),
                        file_path=v.get("file_path"),
                        line_number=v.get("line_number"),
                        context=v.get("context")
                    )
                    for v in result_data.get("violations", [])
                ]
                self.results[name] = QualityGateResult(
                    gate_name=name,
                    passed=result_data["passed"],
                    violations=violations,
                    metrics=result_data.get("metrics", {}),
                    duration_ms=result_data.get("duration_ms", 0)
                )
            logger.info(f"Checkpoint loaded: stage {self.get_current_stage()}")
            return True
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
            return False


class DeerFlowEngine:
    """
    Main entry point for DeerFlow Agent Enforcer.
    Coordinates all components: config, rules, pipeline, skills.
    """

    def __init__(self, config_path: str = "deerflow.yaml", project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.config = DeerFlowConfig(config_path)
        self.rule_engine = RuleEngine(self.config)
        self.orchestrator = PipelineOrchestrator(self.config)
        logger.info(f"DeerFlow Engine v{self.config.version} initialized")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Enforcement level: {self.config.enforcement_level}")

    def scan_project(self) -> List[Violation]:
        """Scan entire project for violations."""
        all_violations = []
        source_dirs = ["src", "app", "lib", "components", "pages", "api"]
        extensions = (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs")

        for source_dir in source_dirs:
            dir_path = self.project_root / source_dir
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if file_path.suffix in extensions:
                        violations = self.rule_engine.check_file(str(file_path))
                        all_violations.extend(violations)

        logger.info(f"Scan complete: {len(all_violations)} violations found")
        return all_violations

    def enforce(self) -> dict:
        """Run full enforcement pipeline."""
        logger.info("Starting full enforcement pipeline...")

        # Stage 1: Scan
        violations = self.scan_project()

        # Stage 2: Build check
        build_dirs = ["dist", "build", ".next", "out"]
        for build_dir in build_dirs:
            build_path = self.project_root / build_dir
            if build_path.exists():
                build_violations = self.rule_engine.check_build_size(str(build_path))
                violations.extend(build_violations)
                break

        # Generate report
        report = self.orchestrator.get_report()
        report["scan_violations"] = [v.to_dict() for v in violations]

        # Save report
        report_path = self.project_root / ".deerflow-report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        logger.info(f"Report saved: {report_path}")

        return report

    def validate_task(self, task_description: str) -> dict:
        """Validate a task against DeerFlow rules before execution."""
        analysis = {
            "task": task_description,
            "timestamp": datetime.now().isoformat(),
            "checks": []
        }

        # Check for destructive patterns
        destructive_keywords = ["delete", "remove", "clean", "wipe", "purge"]
        for kw in destructive_keywords:
            if kw in task_description.lower():
                analysis["checks"].append({
                    "check": "destructive_operation",
                    "passed": False,
                    "message": f"Task contains destructive keyword '{kw}' — requires confirmation"
                })

        return analysis


# === CLI Interface ===
def main():
    """CLI entry point for DeerFlow Agent Enforcer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DeerFlow Agent Enforcer v2.0.0 — Strict AI Agent Quality Framework"
    )
    parser.add_argument("command", choices=["scan", "enforce", "report", "validate"],
                        help="Command to execute")
    parser.add_argument("--config", default="deerflow.yaml", help="Config file path")
    parser.add_argument("--project", default=".", help="Project root directory")
    parser.add_argument("--task", help="Task description for validation")
    parser.add_argument("--output", help="Output file for report")

    args = parser.parse_args()

    engine = DeerFlowEngine(config_path=args.config, project_root=args.project)

    if args.command == "scan":
        violations = engine.scan_project()
        print(f"\nFound {len(violations)} violations:")
        for v in violations:
            print(f"  [{v.severity.value.upper()}] {v.message}")
            if v.file_path:
                print(f"    at {v.file_path}:{v.line_number}")

    elif args.command == "enforce":
        report = engine.enforce()
        print(f"\nEnforcement complete:")
        print(f"  Gates passed: {report['summary']['passed']}")
        print(f"  Gates failed: {report['summary']['failed']}")
        print(f"  Violations: {report['summary']['total_violations']}")
        if not report['summary']['can_proceed']:
            print(f"  STATUS: BLOCKED — Fix violations before proceeding")
            sys.exit(1)

    elif args.command == "report":
        report = engine.orchestrator.get_report()
        output_path = args.output or ".deerflow-report.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {output_path}")

    elif args.command == "validate":
        if not args.task:
            print("Error: --task is required for validate command")
            sys.exit(1)
        result = engine.validate_task(args.task)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
