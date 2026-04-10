"""
DeerFlow Agent Enforcer — Root conftest.py
Shared fixtures for all test suites.
Uses REAL files via tmp_path — no mocks, no fakes.
"""

import os
import sys
import json
import textwrap
from pathlib import Path

import pytest
import yaml

# Ensure the package is importable
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# FIXTURES: DeerFlowConfig with real YAML files
# ============================================================

@pytest.fixture
def repo_root():
    """Absolute path to the repository root."""
    return REPO_ROOT


@pytest.fixture
def full_config_path(repo_root):
    """Path to the project's real deerflow.yaml."""
    return repo_root / "deerflow.yaml"


@pytest.fixture
def strict_config_data():
    """Valid full config matching the real deerflow.yaml schema."""
    return {
        "version": "2.0.0",
        "name": "DeerFlow Agent Enforcer",
        "description": "Test config",
        "project": {
            "min_build_size_kb": 100,
            "max_function_lines": 50,
            "max_complexity": 10,
            "test_coverage_minimum": 80,
            "max_bundle_size_mb": 5,
            "timeout_async_ms": 30000,
            "retry_attempts": 3,
        },
        "enforcement": {
            "level": "strict",
            "auto_fix": True,
            "block_on_violation": True,
            "require_test_pass": True,
            "require_build_pass": True,
            "require_security_pass": True,
        },
        "rules": {
            "file_safety": {
                "severity": "critical",
                "message": "File deletion requires explicit confirmation",
                "action": "block",
            },
            "no_mocks": {
                "severity": "critical",
                "message": "No mock/placeholder code in production",
                "action": "block",
            },
        },
        "quality_gates": {
            "pre_commit": ["lint", "type_check", "unit_tests"],
            "pre_push": ["unit_tests", "security_audit"],
            "continuous": ["build", "security_audit"],
        },
        "skills": {
            "enabled": ["coding", "testing", "security"],
            "coding": {
                "rules": ["strict_typing", "no_prohibited_patterns"],
                "constraints": ["NO mock data"],
            },
            "testing": {
                "rules": ["unit_tests_for_all_functions"],
                "constraints": ["Every function MUST have a test"],
            },
        },
        "agents": {
            "cursor": {"config_file": ".cursorrules", "enabled": True},
            "claude": {"config_file": "CLAUDE.md", "enabled": True},
        },
        "security": {
            "scan_on_commit": True,
            "scan_on_push": True,
            "blocked_patterns": ["password", "secret", "api_key"],
            "env_file_patterns": [".env", ".env.local"],
        },
    }


@pytest.fixture
def minimal_config_data():
    """Minimal valid config with only version."""
    return {"version": "2.0.0"}


@pytest.fixture
def empty_config_file(tmp_path):
    """Create an empty YAML config file."""
    f = tmp_path / "empty.yaml"
    f.write_text("", encoding="utf-8")
    return f


@pytest.fixture
def strict_config_file(tmp_path, strict_config_data):
    """Create a real strict YAML config on disk."""
    f = tmp_path / "strict.yaml"
    f.write_text(yaml.dump(strict_config_data), encoding="utf-8")
    return f


@pytest.fixture
def minimal_config_file(tmp_path, minimal_config_data):
    """Create a minimal YAML config on disk."""
    f = tmp_path / "minimal.yaml"
    f.write_text(yaml.dump(minimal_config_data), encoding="utf-8")
    return f


@pytest.fixture
def nonexistent_config(tmp_path):
    """Path that does not exist."""
    return tmp_path / "does_not_exist.yaml"


# ============================================================
# FIXTURES: Real source code files for RuleEngine tests
# ============================================================

@pytest.fixture
def clean_typescript_file(tmp_path):
    """A real, clean TypeScript file with zero violations."""
    f = tmp_path / "clean.ts"
    f.write_text(
        textwrap.dedent("""\
        interface User {
            id: string;
            name: string;
            email: string;
        }

        async function fetchUser(id: string): Promise<User> {
            const response = await fetch(`/api/users/${id}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch user: ${response.status}`);
            }
            return response.json() as Promise<User>;
        }

        function validateEmail(email: string): boolean {
            const pattern = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
            return pattern.test(email);
        }
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture
def violated_typescript_file(tmp_path):
    """A TypeScript file with MULTIPLE real violations."""
    f = tmp_path / "violated.ts"
    f.write_text(
        textwrap.dedent("""\
        // TODO: implement this later
        const dummy_data = { name: "fake" };

        function processData(input: any): any {
            console.log("debugging", input);
            eval("return " + input);
            // @ts-ignore
            const result = JSON.parse(input);
            // implement this properly
            const password = "admin123";
            return result;
        }
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture
def secret_python_file(tmp_path):
    """A Python file with hardcoded secrets."""
    f = tmp_path / "config.py"
    f.write_text(
        textwrap.dedent("""\
        DB_PASSWORD = "super_secret_pass_123"
        api_key = "sk-abc123def456"
        private_key = "-----BEGIN RSA PRIVATE KEY-----"
        token = "ghp_xxxxxxxxxxxxxxxxxxxx"

        def get_connection():
            return connect(
                host="localhost",
                password="admin123"
            )
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture
def console_log_js_file(tmp_path):
    """A JS file with console.log statements."""
    f = tmp_path / "logger.js"
    f.write_text(
        textwrap.dedent("""\
        function handleClick(event) {
            console.log("Button clicked", event);
            console.debug("Event details:", event.target);
            console.info("Navigation triggered");
            return true;
        }
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture
def clean_python_file(tmp_path):
    """A clean Python file with no violations."""
    f = tmp_path / "utils.py"
    f.write_text(
        textwrap.dedent("""\
        import os
        from typing import Optional

        def get_env(key: str, default: Optional[str] = None) -> str:
            value = os.environ.get(key)
            if value is None:
                if default is not None:
                    return default
                raise ValueError(f"Environment variable {key!r} is not set")
            return value

        def calculate_checksum(data: bytes) -> str:
            import hashlib
            return hashlib.sha256(data).hexdigest()
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture
def long_function_file(tmp_path):
    """A file with a function exceeding 50 lines."""
    lines = ["def very_long_function(x, y, z):"]
    for i in range(55):
        lines.append(f"    result_{i} = x * y + z * {i}")
    lines.append("    return sum([result_{} for _ in range(10)])")
    f = tmp_path / "long_func.py"
    f.write_text("\n".join(lines), encoding="utf-8")
    return f


@pytest.fixture
def eval_danger_file(tmp_path):
    """A file using eval() — critical security violation."""
    f = tmp_path / "dangerous.py"
    f.write_text(
        textwrap.dedent("""\
        def execute_user_input(user_input: str):
            # SECURITY: eval is extremely dangerous
            result = eval(user_input)
            return result
        """),
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tsx_accessibility_file(tmp_path):
    """A TSX file with accessibility issues."""
    f = tmp_path / "BadComponent.tsx"
    f.write_text(
        textwrap.dedent("""\
        export function BadComponent() {
            return (
                <div>
                    <img src="/banner.jpg" />
                    <div onClick={() => alert('clicked')}>
                        Click me
                    </div>
                </div>
            );
        }
        """),
        encoding="utf-8",
    )
    return f


# ============================================================
# FIXTURES: Build directory structures
# ============================================================

@pytest.fixture
def large_build_dir(tmp_path):
    """A build directory with realistic size (> 100KB)."""
    build = tmp_path / "dist"
    build.mkdir()
    # Create files totaling ~150KB
    (build / "index.html").write_bytes(b"<html>" + b"x" * 100000 + b"</html>")
    (build / "app.js").write_bytes(b"// app code" + b"a" * 50000)
    (build / "styles.css").write_bytes(b"body{}" + b"c" * 2000)
    return build


@pytest.fixture
def tiny_build_dir(tmp_path):
    """A build directory that is suspiciously small (< 10KB)."""
    build = tmp_path / "dist"
    build.mkdir()
    (build / "index.html").write_bytes(b"<html></html>")
    return build


@pytest.fixture
def missing_build_dir(tmp_path):
    """Path where no build directory exists."""
    return tmp_path / "nonexistent_dist"


# ============================================================
# FIXTURES: Context Manager test data
# ============================================================

@pytest.fixture
def context_dir(tmp_path):
    """Create a real .deerflow/context directory."""
    d = tmp_path / ".deerflow" / "context"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def existing_decision_data(context_dir):
    """Write a real decisions.json file to disk."""
    data = {
        "decisions": [
            {
                "id": "abc12345",
                "timestamp": "2026-04-10T12:00:00",
                "context": "Authentication flow",
                "decision": "Use JWT with refresh tokens",
                "rationale": "Stateless, scalable, widely supported",
                "consequences": ["Client must store token", "Server needs token rotation"],
                "status": "active",
            },
            {
                "id": "def67890",
                "timestamp": "2026-04-10T13:00:00",
                "context": "Database choice",
                "decision": "PostgreSQL with Prisma ORM",
                "rationale": "Type safety, migrations, excellent TypeScript support",
                "consequences": ["Requires migration files", "Schema needs careful design"],
                "status": "active",
            },
        ],
        "updated_at": "2026-04-10T13:00:00",
        "version": "2.0.0",
    }
    (context_dir / "decisions.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    return data


# ============================================================
# FIXTURES: YAML skill files
# ============================================================

@pytest.fixture
def custom_skill_yaml(tmp_path):
    """Create a real custom skill YAML file on disk."""
    skill_file = tmp_path / "custom_skill.yaml"
    skill_file.write_text(
        textwrap.dedent("""\
        name: performance
        version: "1.5.0"
        description: "Performance optimization skill"
        category: optimization
        rules:
          - lazy_load_routes
          - cache_frequently
          - optimize_images
        constraints:
          - "Bundle size must be < 2MB"
          - "First contentful paint < 1.5s"
        validation_checks:
          - lighthouse_score_above_90
          - bundle_size_checked
        required_tools:
          - lighthouse
          - webpack_analyzer
        required_knowledge:
          - "Web Vitals (LCP, FID, CLS)"
          - "Code splitting strategies"
        priority: 2
        enabled: true
        """),
        encoding="utf-8",
    )
    return skill_file
