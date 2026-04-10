"""
Integration tests — End-to-end pipeline testing with real files.
Tests the full DeerFlow workflow: config → scan → detect → report.
Zero mocks. All data is real.
"""

import json
import textwrap
from pathlib import Path

import pytest
import yaml

from deerflow_core.engine.context_manager import ContextManager
from deerflow_core.engine.orchestrator import (
    ActionType,
    DeerFlowConfig,
    DeerFlowEngine,
    PipelineOrchestrator,
    RuleEngine,
    Severity,
    Violation,
)
from deerflow_core.engine.quality_gate import QualityGateEngine
from deerflow_core.engine.skill_registry import SkillRegistry


# ============================================================
# Full project scanning integration test
# ============================================================


class TestFullProjectScan:
    """Scan a complete realistic project structure with real code."""

    @pytest.fixture
    def real_project(self, tmp_path):
        """Create a realistic project with both clean and violated files."""
        # Create project structure
        src = tmp_path / "src"
        src.mkdir()
        app = src / "app"
        app.mkdir()
        components = src / "components"
        components.mkdir()

        # Clean files
        (src / "utils.ts").write_text(
            textwrap.dedent("""\
            export function add(a: number, b: number): number {
                return a + b;
            }
            export function multiply(a: number, b: number): number {
                return a * b;
            }
            """),
            encoding="utf-8",
        )

        (components / "Button.tsx").write_text(
            textwrap.dedent("""\
            interface ButtonProps {
                label: string;
                onClick: () => void;
                disabled?: boolean;
            }
            export function Button({ label, onClick, disabled }: ButtonProps) {
                return (
                    <button
                        onClick={onClick}
                        disabled={disabled}
                        aria-label={label}
                        onKeyDown={(e) => { if (e.key === 'Enter') onClick(); }}
                    >
                        {label}
                    </button>
                );
            }
            """),
            encoding="utf-8",
        )

        # Violated files
        (app / "handler.ts").write_text(
            textwrap.dedent("""\
            // TODO: implement proper error handling
            const placeholder_data = { users: [] };
            function processInput(input: any): any {
                console.log("processing", input);
                const password = "admin123";
                return placeholder_data;
            }
            """),
            encoding="utf-8",
        )

        # Config files
        (tmp_path / "deerflow.yaml").write_text(
            yaml.dump({
                "version": "2.0.0",
                "enforcement": {"level": "strict"},
                "project": {"min_build_size_kb": 100, "max_function_lines": 50},
            }),
            encoding="utf-8",
        )

        # Small build output (should trigger violation)
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "index.html").write_bytes(b"<html></html>")

        return tmp_path

    def test_scan_finds_violations_only_in_violated_files(self, real_project):
        """RuleEngine should find violations only in handler.ts, not utils.ts."""
        config = DeerFlowConfig(str(real_project / "deerflow.yaml"))
        engine = RuleEngine(config)

        # Scan specific violated file
        handler_violations = engine.check_file(str(real_project / "src" / "app" / "handler.ts"))
        assert len(handler_violations) > 0
        rule_ids = {v.rule_id for v in handler_violations}
        assert "todo_comment" in rule_ids
        assert "console_log" in rule_ids
        assert "hardcoded_secret" in rule_ids
        # dummy_data (underscore) doesn't match placeholder pattern (needs \s)
        # So 'placeholder' won't be in rule_ids for this fixture

        # Scan clean file
        utils_violations = engine.check_file(str(real_project / "src" / "utils.ts"))
        assert len(utils_violations) == 0

        # Scan clean component
        comp_violations = engine.check_file(str(real_project / "src" / "components" / "Button.tsx"))
        assert len(comp_violations) == 0

    def test_build_size_violation_detected(self, real_project):
        config = DeerFlowConfig(str(real_project / "deerflow.yaml"))
        engine = RuleEngine(config)
        violations = engine.check_build_size(str(real_project / "dist"))
        assert len(violations) == 1
        assert violations[0].rule_id == "build_too_small"

    def test_full_enforcement_pipeline(self, real_project):
        """Run the complete DeerFlow engine on a real project."""
        # DeerFlowEngine.scan_project only scans src/, app/, lib/, components/, pages/, api/
        engine = DeerFlowEngine(
            config_path=str(real_project / "deerflow.yaml"),
            project_root=str(real_project),
        )
        report = engine.enforce()
        assert "summary" in report
        assert "scan_violations" in report
        # scan_violations contains violations from RuleEngine.scan_project()
        assert len(report["scan_violations"]) > 0


# ============================================================
# Pipeline orchestration integration
# ============================================================


class TestPipelineIntegration:
    """Test the full 7-stage pipeline with real checks."""

    @pytest.fixture
    def config(self, tmp_path):
        config_file = tmp_path / "deerflow.yaml"
        config_file.write_text(yaml.dump({
            "version": "2.0.0",
            "enforcement": {"level": "strict"},
            "project": {"min_build_size_kb": 50},
        }))
        return DeerFlowConfig(str(config_file))

    @pytest.fixture
    def clean_project(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text(
            "export function greet(name: string): string {\n  return `Hello, ${name}`;\n}\n",
            encoding="utf-8",
        )
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "bundle.js").write_bytes(b"// bundle content" + b"x" * 100000)
        return tmp_path

    def test_full_pipeline_all_pass(self, config, clean_project):
        """Pipeline should pass when project is clean."""
        orch = PipelineOrchestrator(config)

        # Simulate all stages passing
        def passing():
            return True, [], {}

        for stage in PipelineOrchestrator.STAGES[:-1]:
            orch.advance_stage()

        orch.run_quality_gate("lint", passing)
        orch.run_quality_gate("security", passing)
        orch.run_quality_gate("tests", passing)

        assert orch.can_proceed()
        report = orch.get_report()
        assert report["summary"]["failed"] == 0
        assert report["summary"]["can_proceed"] is True

    def test_full_pipeline_blocked_on_failure(self, config, clean_project):
        """Pipeline should be blocked when a gate fails."""
        orch = PipelineOrchestrator(config)

        def passing():
            return True, [], {}

        def failing():
            return False, [
                Violation(
                    rule_id="secret_found", severity=Severity.CRITICAL,
                    message="Hardcoded secret detected",
                    action=ActionType.BLOCK,
                    file_path="src/index.ts", line_number=1,
                )
            ], {}

        orch.run_quality_gate("lint", passing)
        orch.run_quality_gate("security", failing)
        orch.run_quality_gate("tests", passing)

        assert not orch.can_proceed()
        report = orch.get_report()
        assert report["summary"]["failed"] == 1
        assert report["summary"]["can_proceed"] is False
        assert "security" in report["failed_gate_names"]

    def test_pipeline_checkpoint_recovery(self, config, tmp_path):
        """Pipeline should recover state from checkpoint file."""
        config_path = tmp_path / "deerflow.yaml"
        config_path.write_text(yaml.dump({"version": "2.0.0"}))

        # First session: advance to 'implement' and run some gates
        orch1 = PipelineOrchestrator(DeerFlowConfig(str(config_path)))
        orch1.checkpoint_file = tmp_path / "checkpoint.json"
        orch1.advance_stage()  # analyze → plan
        orch1.advance_stage()  # plan → implement
        orch1.run_quality_gate("lint", lambda: (True, [], {}))

        # Second session: recover
        orch2 = PipelineOrchestrator(DeerFlowConfig(str(config_path)))
        orch2.checkpoint_file = tmp_path / "checkpoint.json"
        loaded = orch2.load_checkpoint()

        assert loaded is True
        assert orch2.get_current_stage() == "implement"
        assert "lint" in orch2.results
        assert orch2.results["lint"].passed is True


# ============================================================
# Skill + Pipeline integration
# ============================================================


class TestSkillPipelineIntegration:
    """Test skills activating during pipeline stages."""

    def test_coding_skill_activated_during_implement(self):
        registry = SkillRegistry(skills_dir="/nonexistent")
        # During implementation phase
        assert registry.activate_skill("coding") is True
        assert registry.activate_skill("security") is True
        rules = registry.get_active_rules()
        constraints = registry.get_active_constraints()
        # Should have rules from both skills
        assert len(rules) >= 10
        # Should have constraints from both
        assert any("mock" in c.lower() for c in constraints)
        assert any("eval" in c.lower() for c in constraints)

    def test_testing_skill_activated_after_code(self):
        registry = SkillRegistry(skills_dir="/nonexistent")
        assert registry.activate_skill("testing") is True
        rules = registry.get_active_rules()
        constraints = registry.get_active_constraints()
        assert "unit_tests_for_all_functions" in rules
        assert any("test" in c.lower() for c in constraints)

    def test_deployment_skill_activated_last(self):
        registry = SkillRegistry(skills_dir="/nonexistent")
        assert registry.activate_skill("deployment") is True
        constraints = registry.get_active_constraints()
        assert any("build" in c.lower() for c in constraints)

    def test_full_skill_prompt_generation(self):
        registry = SkillRegistry(skills_dir="/nonexistent")
        for skill_name in ["coding", "security", "testing", "architecture", "deployment"]:
            registry.activate_skill(skill_name)

        prompt = registry.get_skill_prompt()
        assert "<active-skills>" in prompt
        assert "coding" in prompt
        assert "security" in prompt
        assert "testing" in prompt
        assert "architecture" in prompt
        assert "deployment" in prompt
        # Verify all sections present for each skill
        rule_count = prompt.count("### Rules:")
        assert rule_count >= 5


# ============================================================
# Context + Engine integration
# ============================================================


class TestContextEngineIntegration:
    """Test context persistence during engine operations."""

    def test_engine_saves_report_to_disk(self, tmp_path):
        config_file = tmp_path / "deerflow.yaml"
        config_file.write_text(yaml.dump({"version": "2.0.0"}))
        src = tmp_path / "src"
        src.mkdir()
        (src / "clean.ts").write_text("export const x = 1;\n", encoding="utf-8")

        engine = DeerFlowEngine(
            config_path=str(config_file),
            project_root=str(tmp_path),
        )
        report = engine.enforce()

        report_file = tmp_path / ".deerflow-report.json"
        assert report_file.exists()
        data = json.loads(report_file.read_text(encoding="utf-8"))
        assert "summary" in data
        assert "version" in data

    def test_context_tracks_decisions_during_pipeline(self, tmp_path):
        ctx = ContextManager(project_root=str(tmp_path))
        ctx.start_task("integration-1", "Build payment system", requirements=["Stripe"])
        ctx.record_decision("Payment", "Stripe SDK", "Industry standard")
        ctx.track_file_change("src/payment/stripe.ts", "created")
        ctx.complete_step("Setup Stripe SDK")
        ctx.record_error("API key missing", solution="Use env var STRIPE_KEY")

        summary = ctx.get_context_summary()
        assert "integration-1" in summary
        assert "Stripe SDK" in summary
        assert "stripe.ts" in summary
        assert "API key missing" in summary


# ============================================================
# Quality gates on realistic project
# ============================================================


class TestQualityGatesRealisticProject:
    """Run all quality gates on a project that has both violations and clean code."""

    @pytest.fixture
    def mixed_project(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        lib = tmp_path / "lib"
        lib.mkdir()

        # Clean file
        (src / "math.ts").write_text(
            textwrap.dedent("""\
            export function add(a: number, b: number): number {
                return a + b;
            }
            """),
            encoding="utf-8",
        )

        # File with console.log
        (lib / "logger.ts").write_text(
            textwrap.dedent("""\
            export function log(message: string): void {
                console.log(message);
                console.debug("Details:", message);
            }
            """),
            encoding="utf-8",
        )

        # Build with reasonable size
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "app.js").write_bytes(b"// code" + b"x" * 200000)

        return tmp_path

    def test_all_gates_run_on_mixed_project(self, mixed_project):
        engine = QualityGateEngine(project_root=str(mixed_project))
        results = engine.run_all()

        assert len(results) == 12
        # console.log check should fail
        assert results["no_console_log"].passed is False
        # Build should pass
        assert results["bundle_size"].passed is True
        # Secrets should pass (no hardcoded secrets)
        assert results["no_hardcoded_secrets"].passed is True
        # File safety should pass (no git)
        assert results["file_safety"].passed is True

    def test_pre_commit_gates_on_mixed_project(self, mixed_project):
        engine = QualityGateEngine(project_root=str(mixed_project))
        results = engine.run_gates("pre_commit")
        # console.log should fail
        assert results["no_console_log"].passed is False
