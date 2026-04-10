"""
DeerFlow Agent Enforcer — Context Manager
Manages conversation context, decision tracking, and knowledge persistence.
Prevents context drift and ensures long-running tasks maintain coherence.
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger('deerflow.context')


@dataclass
class Decision:
    """Records an architectural or design decision."""
    id: str
    timestamp: str
    context: str
    decision: str
    rationale: str
    consequences: List[str] = field(default_factory=list)
    status: str = "active"  # active | superseded | reverted


@dataclass
class TaskMemory:
    """Tracks task progress and key information."""
    task_id: str
    description: str
    started_at: str
    status: str = "in_progress"
    requirements: List[str] = field(default_factory=list)
    architecture_decisions: List[Decision] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    errors_encountered: List[dict] = field(default_factory=list)
    solutions_applied: List[str] = field(default_factory=list)
    current_focus: str = ""
    blocked_by: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)


class ContextManager:
    """
    Manages AI agent context to prevent drift and knowledge loss.
    Inspired by DeerFlow's persistent memory layer with PostgreSQL checkpoints.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.context_dir = self.project_root / ".deerflow" / "context"
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.current_task: Optional[TaskMemory] = None
        self.decision_log: List[Decision] = []
        self._load_context()

    def _load_context(self) -> None:
        """Load existing context from disk."""
        context_file = self.context_dir / "decisions.json"
        if context_file.exists():
            try:
                data = json.loads(context_file.read_text(encoding='utf-8'))
                self.decision_log = [
                    Decision(**d) for d in data.get("decisions", [])
                ]
                logger.info(f"Loaded {len(self.decision_log)} decisions from context")
            except Exception as e:
                logger.warning(f"Failed to load context: {e}")

    def _save_context(self) -> None:
        """Save context to disk for persistence."""
        context_file = self.context_dir / "decisions.json"
        data = {
            "decisions": [d.__dict__ for d in self.decision_log],
            "updated_at": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        try:
            context_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save context: {e}")

    def start_task(self, task_id: str, description: str, requirements: List[str] = None) -> TaskMemory:
        """Start tracking a new task."""
        task = TaskMemory(
            task_id=task_id,
            description=description,
            started_at=datetime.now().isoformat(),
            requirements=requirements or []
        )
        self.current_task = task

        # Save task to disk
        task_file = self.context_dir / f"task_{task_id}.json"
        task_file.write_text(json.dumps(task.__dict__, indent=2, default=str), encoding='utf-8')
        logger.info(f"Task started: {task_id} — {description[:100]}")
        return task

    def record_decision(self, context: str, decision: str, rationale: str,
                        consequences: List[str] = None) -> Decision:
        """Record an architectural or design decision."""
        decision_id = hashlib.md5(f"{context}:{decision}".encode()).hexdigest()[:8]
        dec = Decision(
            id=decision_id,
            timestamp=datetime.now().isoformat(),
            context=context,
            decision=decision,
            rationale=rationale,
            consequences=consequences or []
        )
        self.decision_log.append(dec)
        self._save_context()

        if self.current_task:
            self.current_task.architecture_decisions.append(dec)

        logger.info(f"Decision recorded: {decision_id} — {decision[:80]}")
        return dec

    def track_file_change(self, file_path: str, action: str = "modified") -> None:
        """Track file modifications for context awareness."""
        if not self.current_task:
            return

        if action == "created" and file_path not in self.current_task.files_created:
            self.current_task.files_created.append(file_path)
        elif action == "modified" and file_path not in self.current_task.files_modified:
            self.current_task.files_modified.append(file_path)

        self._save_task()

    def record_error(self, error: str, solution: str = "", file_path: str = "") -> None:
        """Record an error encountered and its solution."""
        if not self.current_task:
            return

        self.current_task.errors_encountered.append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "solution": solution,
            "file_path": file_path
        })

        if solution:
            self.current_task.solutions_applied.append(solution)

        self._save_task()

    def complete_step(self, step: str) -> None:
        """Mark a step as completed."""
        if not self.current_task:
            return
        if step in self.current_task.pending_steps:
            self.current_task.pending_steps.remove(step)
        if step not in self.current_task.completed_steps:
            self.current_task.completed_steps.append(step)
        self._save_task()

    def get_context_summary(self) -> str:
        """Generate a context summary for the AI agent."""
        if not self.current_task:
            return "No active task context."

        lines = [
            f"<task-context>",
            f"<task-id>{self.current_task.task_id}</task-id>",
            f"<description>{self.current_task.description}</description>",
            f"<started>{self.current_task.started_at}</started>",
            f"<status>{self.current_task.status}</status>",
        ]

        if self.current_task.requirements:
            lines.append("<requirements>")
            for req in self.current_task.requirements:
                lines.append(f"  - {req}")
            lines.append("</requirements>")

        if self.current_task.architecture_decisions:
            lines.append("<decisions>")
            for dec in self.current_task.architecture_decisions[-10:]:  # Last 10 decisions
                lines.append(f"  [{dec.id}] {dec.decision}")
                lines.append(f"    Rationale: {dec.rationale}")
            lines.append("</decisions>")

        if self.current_task.errors_encountered:
            lines.append("<errors-and-solutions>")
            for err in self.current_task.errors_encountered[-5:]:  # Last 5 errors
                lines.append(f"  Error: {err['error'][:100]}")
                if err['solution']:
                    lines.append(f"  Solution: {err['solution'][:100]}")
            lines.append("</errors-and-solutions>")

        if self.current_task.files_modified:
            lines.append("<files-modified>")
            for f in self.current_task.files_modified[-20:]:
                lines.append(f"  - {f}")
            lines.append("</files-modified>")

        if self.current_task.files_created:
            lines.append("<files-created>")
            for f in self.current_task.files_created[-20:]:
                lines.append(f"  - {f}")
            lines.append("</files-created>")

        if self.current_task.completed_steps:
            lines.append("<completed-steps>")
            for step in self.current_task.completed_steps:
                lines.append(f"  ✓ {step}")
            lines.append("</completed-steps>")

        if self.current_task.pending_steps:
            lines.append("<pending-steps>")
            for step in self.current_task.pending_steps:
                lines.append(f"  ○ {step}")
            lines.append("</pending-steps>")

        lines.append("</task-context>")
        return "\n".join(lines)

    def get_decision_history(self, limit: int = 20) -> List[Decision]:
        """Get recent decision history."""
        return self.decision_log[-limit:]

    def _save_task(self) -> None:
        """Save current task state."""
        if not self.current_task:
            return
        task_file = self.context_dir / f"task_{self.current_task.task_id}.json"
        task_file.write_text(
            json.dumps(self.current_task.__dict__, indent=2, default=str),
            encoding='utf-8'
        )
