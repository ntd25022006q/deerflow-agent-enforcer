"""
Unit tests for context_manager.py — ContextManager, Decision, TaskMemory.
Uses real file I/O via tmp_path — zero mocks.
"""

import hashlib
import json
from pathlib import Path

import pytest

from deerflow_core.engine.context_manager import ContextManager, Decision, TaskMemory


# ============================================================
# Decision dataclass tests
# ============================================================


class TestDecision:

    def test_creation_with_required_fields(self):
        d = Decision(
            id="abc123", timestamp="2026-04-10T12:00:00",
            context="Auth", decision="Use JWT",
            rationale="Stateless",
        )
        assert d.id == "abc123"
        assert d.status == "active"
        assert d.consequences == []

    def test_creation_with_all_fields(self):
        d = Decision(
            id="def456", timestamp="2026-04-10T13:00:00",
            context="DB", decision="PostgreSQL",
            rationale="ACID compliance",
            consequences=["Need migration tool", "Connection pooling"],
            status="active",
        )
        assert len(d.consequences) == 2

    def test_default_status_is_active(self):
        d = Decision(id="x", timestamp="t", context="c", decision="d", rationale="r")
        assert d.status == "active"


# ============================================================
# TaskMemory dataclass tests
# ============================================================


class TestTaskMemory:

    def test_creation_with_defaults(self):
        t = TaskMemory(task_id="task-1", description="Build auth", started_at="2026-04-10")
        assert t.status == "in_progress"
        assert t.requirements == []
        assert t.files_modified == []
        assert t.errors_encountered == []
        assert t.completed_steps == []
        assert t.pending_steps == []

    def test_creation_with_all_fields(self):
        dec = Decision(id="d1", timestamp="t", context="c", decision="d", rationale="r")
        t = TaskMemory(
            task_id="task-2", description="Create API",
            started_at="2026-04-10T14:00:00",
            status="in_progress",
            requirements=["REST endpoints", "Auth middleware"],
            architecture_decisions=[dec],
            files_modified=["src/api/handler.ts"],
            files_created=["src/api/routes.ts"],
            errors_encountered=[{"error": "Type error", "solution": "Add generic"}],
            solutions_applied=["Add generic <T>"],
            current_focus="Implementing POST endpoint",
            blocked_by=["Waiting for DB schema"],
            completed_steps=["Design API", "Setup routes"],
            pending_steps=["Implement handlers", "Add tests"],
        )
        assert len(t.requirements) == 2
        assert len(t.architecture_decisions) == 1
        assert len(t.completed_steps) == 2
        assert len(t.pending_steps) == 2

    def test_task_memory_serializable(self):
        t = TaskMemory(
            task_id="task-3", description="Test task",
            started_at="2026-04-10",
            pending_steps=["Step 1"],
        )
        # Must be JSON-serializable (used in save/load)
        data = json.dumps(t.__dict__, default=str)
        parsed = json.loads(data)
        assert parsed["task_id"] == "task-3"


# ============================================================
# ContextManager tests — real file I/O
# ============================================================


class TestContextManager:

    @pytest.fixture
    def manager(self, tmp_path):
        return ContextManager(project_root=str(tmp_path))

    def test_initializes_with_empty_state(self, manager):
        assert manager.current_task is None
        assert manager.decision_log == []

    def test_creates_context_directory(self, manager, tmp_path):
        assert (tmp_path / ".deerflow" / "context").exists()

    def test_start_task_creates_task(self, manager):
        task = manager.start_task("t1", "Build login page")
        assert task is not None
        assert task.task_id == "t1"
        assert task.description == "Build login page"
        assert task.status == "in_progress"
        assert manager.current_task is not None

    def test_start_task_with_requirements(self, manager):
        task = manager.start_task(
            "t2", "Create API",
            requirements=["REST", "Auth", "Validation"],
        )
        assert len(task.requirements) == 3

    def test_start_task_saves_to_disk(self, manager, tmp_path):
        manager.start_task("t3", "Test task")
        task_file = tmp_path / ".deerflow" / "context" / "task_t3.json"
        assert task_file.exists()
        data = json.loads(task_file.read_text(encoding="utf-8"))
        assert data["task_id"] == "t3"

    def test_record_decision(self, manager):
        dec = manager.record_decision(
            context="Authentication",
            decision="Use JWT tokens",
            rationale="Stateless, scalable",
            consequences=["Client stores token"],
        )
        assert dec.id is not None
        assert len(dec.id) == 8  # MD5 hex digest first 8 chars
        assert dec.timestamp is not None
        assert len(manager.decision_log) == 1
        assert manager.decision_log[0].decision == "Use JWT tokens"

    def test_record_decision_deterministic_id(self, manager):
        d1 = manager.record_decision("ctx", "Use React", "Because")
        d2 = manager.record_decision("ctx", "Use React", "Because")
        # MD5 of same context+decision should produce same id
        assert d1.id == d2.id

    def test_record_decision_different_inputs_different_id(self, manager):
        d1 = manager.record_decision("ctx", "Use React", "Because")
        d2 = manager.record_decision("ctx2", "Use Vue", "Because2")
        assert d1.id != d2.id

    def test_record_decision_saves_to_disk(self, manager, tmp_path):
        manager.record_decision("Auth", "JWT", "Stateless")
        decisions_file = tmp_path / ".deerflow" / "context" / "decisions.json"
        assert decisions_file.exists()
        data = json.loads(decisions_file.read_text(encoding="utf-8"))
        assert len(data["decisions"]) == 1
        assert data["decisions"][0]["decision"] == "JWT"

    def test_record_decision_appends_to_task(self, manager):
        manager.start_task("t4", "Test")
        manager.record_decision("DB", "PostgreSQL", "ACID")
        assert len(manager.current_task.architecture_decisions) == 1

    def test_record_decision_without_task(self, manager):
        dec = manager.record_decision("Style", "CSS Modules", "Scoping")
        assert len(manager.decision_log) == 1
        # No error, just doesn't append to task

    def test_track_file_change_created(self, manager):
        manager.start_task("t5", "Track files")
        manager.track_file_change("src/new_file.ts", "created")
        assert "src/new_file.ts" in manager.current_task.files_created

    def test_track_file_change_modified(self, manager):
        manager.start_task("t6", "Track files")
        manager.track_file_change("src/existing.ts", "modified")
        assert "src/existing.ts" in manager.current_task.files_modified

    def test_track_file_change_no_duplicates(self, manager):
        manager.start_task("t7", "Track files")
        manager.track_file_change("src/a.ts", "modified")
        manager.track_file_change("src/a.ts", "modified")
        assert manager.current_task.files_modified.count("src/a.ts") == 1

    def test_track_file_change_without_task(self, manager):
        # Should not crash
        manager.track_file_change("src/a.ts", "modified")

    def test_record_error(self, manager):
        manager.start_task("t8", "Error test")
        manager.record_error(
            "TypeScript error: Type 'string' is not assignable to 'number'",
            solution="Add proper type annotation",
            file_path="src/calc.ts",
        )
        assert len(manager.current_task.errors_encountered) == 1
        err = manager.current_task.errors_encountered[0]
        assert "TypeScript" in err["error"]
        assert err["solution"] == "Add proper type annotation"
        assert err["file_path"] == "src/calc.ts"

    def test_record_error_without_solution(self, manager):
        manager.start_task("t9", "Error test")
        manager.record_error("Build failed")
        assert len(manager.current_task.errors_encountered) == 1
        assert len(manager.current_task.solutions_applied) == 0

    def test_record_error_without_task(self, manager):
        manager.record_error("Some error")
        # Should not crash

    def test_complete_step(self, manager):
        manager.start_task("t10", "Steps test")
        manager.current_task.pending_steps = ["Design", "Implement", "Test"]
        manager.complete_step("Design")
        assert "Design" in manager.current_task.completed_steps
        assert "Design" not in manager.current_task.pending_steps

    def test_complete_step_not_in_pending(self, manager):
        manager.start_task("t11", "Steps test")
        manager.complete_step("Already done")
        assert "Already done" in manager.current_task.completed_steps

    def test_complete_step_no_duplicates(self, manager):
        manager.start_task("t12", "Steps test")
        manager.complete_step("A")
        manager.complete_step("A")
        assert manager.current_task.completed_steps.count("A") == 1

    def test_get_context_summary_no_task(self, manager):
        summary = manager.get_context_summary()
        assert "No active task" in summary

    def test_get_context_summary_with_task(self, manager):
        manager.start_task("t13", "Build auth system", requirements=["JWT", "OAuth"])
        manager.current_task.pending_steps = ["Implement login", "Add tests"]
        manager.current_task.completed_steps = ["Design schema"]
        summary = manager.get_context_summary()
        assert "<task-context>" in summary
        assert "</task-context>" in summary
        assert "t13" in summary
        assert "Build auth system" in summary
        assert "JWT" in summary
        assert "Implement login" in summary
        assert "Design schema" in summary

    def test_get_context_summary_with_decisions(self, manager):
        manager.start_task("t14", "Decision test")
        manager.record_decision("Auth", "JWT", "Stateless")
        summary = manager.get_context_summary()
        assert "<decisions>" in summary
        assert "JWT" in summary

    def test_get_context_summary_with_errors(self, manager):
        manager.start_task("t15", "Error summary test")
        manager.record_error("Build failed", solution="Fixed config")
        summary = manager.get_context_summary()
        assert "<errors-and-solutions>" in summary
        assert "Build failed" in summary
        assert "Fixed config" in summary

    def test_get_context_summary_with_files(self, manager):
        manager.start_task("t16", "Files test")
        manager.track_file_change("src/a.ts", "modified")
        manager.track_file_change("src/b.ts", "created")
        summary = manager.get_context_summary()
        assert "<files-modified>" in summary
        assert "src/a.ts" in summary

    def test_get_decision_history(self, manager):
        manager.record_decision("A", "Decision A", "Rationale A")
        manager.record_decision("B", "Decision B", "Rationale B")
        manager.record_decision("C", "Decision C", "Rationale C")
        history = manager.get_decision_history(limit=2)
        assert len(history) == 2
        assert history[0].decision == "Decision B"
        assert history[1].decision == "Decision C"

    def test_load_existing_decisions(self, tmp_path, existing_decision_data):
        """Load real decisions from disk."""
        manager = ContextManager(project_root=str(tmp_path))
        assert len(manager.decision_log) == 2
        assert manager.decision_log[0].decision == "Use JWT with refresh tokens"
        assert manager.decision_log[1].decision == "PostgreSQL with Prisma ORM"

    def test_save_task_persists(self, manager, tmp_path):
        manager.start_task("t17", "Persist test")
        manager.track_file_change("src/x.ts", "modified")
        task_file = tmp_path / ".deerflow" / "context" / "task_t17.json"
        content = task_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert "src/x.ts" in data["files_modified"]

    def test_context_dir_created_if_missing(self, tmp_path):
        # Remove the directory that manager creates
        ctx_dir = tmp_path / ".deerflow" / "context"
        manager = ContextManager(project_root=str(tmp_path))
        assert ctx_dir.exists()


class TestContextManagerPersistence:
    """Tests for context persistence across manager instances."""

    def test_decisions_persist_across_instances(self, tmp_path):
        m1 = ContextManager(project_root=str(tmp_path))
        m1.record_decision("DB", "PostgreSQL", "ACID")
        m1.record_decision("Cache", "Redis", "Performance")

        m2 = ContextManager(project_root=str(tmp_path))
        assert len(m2.decision_log) == 2
        assert m2.decision_log[0].decision == "PostgreSQL"
        assert m2.decision_log[1].decision == "Redis"

    def test_task_state_on_disk(self, tmp_path):
        m1 = ContextManager(project_root=str(tmp_path))
        m1.start_task("persist-1", "Persistent task", requirements=["Req1"])
        m1.complete_step("Req1")
        m1.track_file_change("src/main.ts", "created")

        # Simulate new session
        m2 = ContextManager(project_root=str(tmp_path))
        task_file = tmp_path / ".deerflow" / "context" / "task_persist-1.json"
        assert task_file.exists()
        data = json.loads(task_file.read_text(encoding="utf-8"))
        assert data["description"] == "Persistent task"
        assert "Req1" in data["completed_steps"]
        assert "src/main.ts" in data["files_created"]
