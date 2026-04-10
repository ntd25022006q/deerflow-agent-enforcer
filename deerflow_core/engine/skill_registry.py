"""
DeerFlow Agent Enforcer — Skill Registry
Manages agent skills: loading, validation, and progressive activation.
Based on DeerFlow's progressive skill loading architecture.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger('deerflow.skills')


@dataclass
class SkillDefinition:
    """Definition of an agent skill."""
    name: str
    version: str
    description: str
    category: str
    rules: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    required_knowledge: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    validation_checks: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 5  # 1=highest, 10=lowest

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "rules": self.rules,
            "required_tools": self.required_tools,
            "required_knowledge": self.required_knowledge,
            "constraints": self.constraints,
            "validation_checks": self.validation_checks,
            "enabled": self.enabled,
            "priority": self.priority
        }


class SkillRegistry:
    """
    Registry for managing agent skills.
    Skills are loaded progressively — only what's needed, when it's needed.
    """

    # Built-in skill definitions following DeerFlow patterns
    BUILTIN_SKILLS: Dict[str, SkillDefinition] = {}

    def __init__(self, skills_dir: str = "deerflow-core/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, SkillDefinition] = {}
        self.active_skills: Dict[str, SkillDefinition] = {}
        self._load_builtin_skills()
        self._load_custom_skills()

    def _load_builtin_skills(self) -> None:
        """Load built-in skill definitions."""
        self.BUILTIN_SKILLS = {
            "coding": SkillDefinition(
                name="coding",
                version="2.0.0",
                description="Core coding skill: write production-ready, fully-implemented code",
                category="core",
                rules=[
                    "follow_project_conventions",
                    "strict_typing",
                    "no_prohibited_patterns",
                    "comprehensive_error_handling",
                    "complete_implementation",
                    "no_infinite_loops",
                    "proper_async_handling",
                    "clean_code_principles"
                ],
                required_tools=["linter", "type_checker", "formatter"],
                required_knowledge=[
                    "Language best practices (TypeScript, Python, etc.)",
                    "Design patterns (Factory, Observer, Strategy, etc.)",
                    "SOLID principles",
                    "Error handling patterns",
                    "Testing patterns (AAA, given/when/then)"
                ],
                constraints=[
                    "NO mock data in production code",
                    "NO TODO comments",
                    "NO any type without justification",
                    "Functions must be < 50 lines",
                    "Cyclomatic complexity < 10"
                ],
                validation_checks=[
                    "all_functions_implemented",
                    "no_prohibited_patterns",
                    "type_safety_verified",
                    "error_handling_complete"
                ],
                priority=1
            ),
            "testing": SkillDefinition(
                name="testing",
                version="2.0.0",
                description="Testing skill: write comprehensive tests for all code",
                category="quality",
                rules=[
                    "unit_tests_for_all_functions",
                    "integration_tests_for_apis",
                    "e2e_tests_for_critical_paths",
                    "edge_case_coverage",
                    "no_skipped_tests",
                    "meaningful_assertions"
                ],
                required_tools=["test_runner", "coverage_tool", "mocking_framework"],
                required_knowledge=[
                    "Testing frameworks (Jest, Vitest, Pytest)",
                    "Testing patterns (AAA, given/when/then)",
                    "Mocking and stubbing",
                    "Test organization",
                    "Coverage analysis"
                ],
                constraints=[
                    "Every new function MUST have at least 1 test",
                    "Every component MUST have render test",
                    "Edge cases: null, empty, large, concurrent",
                    "Test names must describe expected behavior"
                ],
                validation_checks=[
                    "coverage_threshold_met",
                    "all_tests_passing",
                    "no_skipped_tests",
                    "edge_cases_covered"
                ],
                priority=2
            ),
            "security": SkillDefinition(
                name="security",
                version="2.0.0",
                description="Security skill: implement secure coding practices",
                category="safety",
                rules=[
                    "no_hardcoded_secrets",
                    "input_validation_required",
                    "xss_prevention",
                    "csrf_protection",
                    "sql_injection_prevention",
                    "dependency_audit",
                    "secure_headers"
                ],
                required_tools=["security_scanner", "dependency_checker", "secret_detector"],
                required_knowledge=[
                    "OWASP Top 10",
                    "CWE/SANS Top 25",
                    "Security headers (CSP, CORS, HSTS)",
                    "Authentication patterns (JWT, OAuth)",
                    "Encryption fundamentals"
                ],
                constraints=[
                    "ALL secrets in environment variables",
                    "Parameterized queries ONLY for SQL",
                    "Sanitize ALL user-provided content",
                    "NO eval(), NO innerHTML with user data",
                    "CORS configured properly"
                ],
                validation_checks=[
                    "no_secrets_in_code",
                    "input_validation_present",
                    "security_headers_configured",
                    "dependency_audit_clean"
                ],
                priority=1
            ),
            "architecture": SkillDefinition(
                name="architecture",
                version="2.0.0",
                description="Architecture skill: design and implement proper software architecture",
                category="design",
                rules=[
                    "plan_before_code",
                    "component_hierarchy",
                    "state_management_strategy",
                    "proper_file_structure",
                    "separation_of_concerns",
                    "dependency_inversion"
                ],
                required_tools=["diagram_generator", "dependency_analyzer"],
                required_knowledge=[
                    "Design patterns (GoF)",
                    "Architecture patterns (MVC, MVVM, Clean Architecture, Hexagonal)",
                    "Domain-driven design",
                    "Microservices patterns",
                    "System design principles"
                ],
                constraints=[
                    "Design before implementation",
                    "Document architecture decisions",
                    "Follow existing project patterns",
                    "Single responsibility per module",
                    "Dependencies point inward (Clean Architecture)"
                ],
                validation_checks=[
                    "architecture_documented",
                    "components_properly_separated",
                    "dependencies_managed",
                    "file_structure_consistent"
                ],
                priority=2
            ),
            "documentation": SkillDefinition(
                name="documentation",
                version="2.0.0",
                description="Documentation skill: write comprehensive documentation",
                category="quality",
                rules=[
                    "inline_comments_for_complexity",
                    "jsdoc_for_public_apis",
                    "adr_for_decisions",
                    "readme_updated",
                    "changelog_maintained"
                ],
                required_tools=[],
                required_knowledge=[
                    "Documentation best practices",
                    "ADR format",
                    "API documentation (OpenAPI/Swagger)",
                    "Technical writing principles"
                ],
                constraints=[
                    "Complex logic: explain WHY, not WHAT",
                    "Public APIs: complete JSDoc/docstrings",
                    "Architecture changes: create ADR",
                    "README: setup, usage, architecture"
                ],
                validation_checks=[
                    "public_apis_documented",
                    "complex_logic_commented",
                    "readme_complete"
                ],
                priority=5
            ),
            "deployment": SkillDefinition(
                name="deployment",
                version="2.0.0",
                description="Deployment skill: prepare code for production deployment",
                category="ops",
                rules=[
                    "build_verification",
                    "env_vars_only_for_secrets",
                    "ci_cd_pipeline_passes",
                    "monitoring_ready",
                    "rollback_strategy"
                ],
                required_tools=["build_tool", "docker", "ci_cd"],
                required_knowledge=[
                    "CI/CD pipelines",
                    "Containerization (Docker)",
                    "Infrastructure as Code",
                    "Monitoring and alerting",
                    "Deployment strategies (blue-green, canary)"
                ],
                constraints=[
                    "Build must include all assets",
                    "Environment variables for ALL config",
                    "Health check endpoints",
                    "Graceful shutdown handling",
                    "Log structured JSON"
                ],
                validation_checks=[
                    "build_complete",
                    "env_vars_configured",
                    "ci_cd_passes",
                    "monitoring_setup"
                ],
                priority=3
            ),
        }
        self.skills.update(self.BUILTIN_SKILLS)

    def _load_custom_skills(self) -> None:
        """Load custom skills from skills directory."""
        if not self.skills_dir.exists():
            return

        for skill_file in self.skills_dir.rglob("*.yaml"):
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    import yaml
                    data = yaml.safe_load(f)
                    if data:
                        skill = SkillDefinition(**data)
                        self.skills[skill.name] = skill
                        logger.info(f"Loaded custom skill: {skill.name}")
            except Exception as e:
                logger.warning(f"Failed to load skill from {skill_file}: {e}")

    def activate_skill(self, skill_name: str) -> bool:
        """Activate a skill for the current task."""
        if skill_name not in self.skills:
            logger.warning(f"Skill not found: {skill_name}")
            return False
        self.active_skills[skill_name] = self.skills[skill_name]
        logger.info(f"Skill activated: {skill_name}")
        return True

    def deactivate_skill(self, skill_name: str) -> bool:
        """Deactivate a skill."""
        if skill_name in self.active_skills:
            del self.active_skills[skill_name]
            logger.info(f"Skill deactivated: {skill_name}")
            return True
        return False

    def get_active_rules(self) -> List[str]:
        """Get all rules from currently active skills."""
        rules = []
        for skill in self.active_skills.values():
            rules.extend(skill.rules)
        return rules

    def get_active_constraints(self) -> List[str]:
        """Get all constraints from currently active skills."""
        constraints = []
        for skill in self.active_skills.values():
            constraints.extend(skill.constraints)
        return constraints

    def get_skill_prompt(self) -> str:
        """Generate a prompt section for active skills."""
        if not self.active_skills:
            return ""

        lines = ["<active-skills>"]
        for name, skill in sorted(self.active_skills.items(), key=lambda x: x[1].priority):
            lines.append(f"\n## Skill: {skill.name} (v{skill.version})")
            lines.append(f"{skill.description}")
            lines.append(f"\n### Rules:")
            for rule in skill.rules:
                lines.append(f"- {rule}")
            lines.append(f"\n### Constraints:")
            for constraint in skill.constraints:
                lines.append(f"- {constraint}")
            lines.append(f"\n### Validation Checks:")
            for check in skill.validation_checks:
                lines.append(f"- [ ] {check}")
        lines.append("</active-skills>")
        return "\n".join(lines)

    def validate_active_skills(self) -> Dict[str, List[str]]:
        """Validate that active skills' requirements are met."""
        results = {}
        for name, skill in self.active_skills.items():
            missing = []
            for tool in skill.required_tools:
                missing.append(f"Tool: {tool}")
            results[name] = missing
        return results

    def list_skills(self) -> List[dict]:
        """List all available skills."""
        return [s.to_dict() for s in sorted(self.skills.values(), key=lambda x: x.priority)]


# === Skill Definitions (YAML format for extensibility) ===

SKILL_YAML_TEMPLATES = {
    "coding": """
name: coding
version: "2.0.0"
description: "Core coding skill: write production-ready, fully-implemented code"
category: core
rules:
  - follow_project_conventions
  - strict_typing
  - no_prohibited_patterns
  - comprehensive_error_handling
  - complete_implementation
  - no_infinite_loops
  - proper_async_handling
  - clean_code_principles
required_tools:
  - linter
  - type_checker
  - formatter
constraints:
  - "NO mock data in production code"
  - "NO TODO comments"
  - "NO any type without justification"
  - "Functions must be < 50 lines"
validation_checks:
  - all_functions_implemented
  - no_prohibited_patterns
  - type_safety_verified
  - error_handling_complete
priority: 1
enabled: true
""",
    "testing": """
name: testing
version: "2.0.0"
description: "Testing skill: write comprehensive tests for all code"
category: quality
rules:
  - unit_tests_for_all_functions
  - integration_tests_for_apis
  - e2e_tests_for_critical_paths
  - edge_case_coverage
  - no_skipped_tests
constraints:
  - "Every new function MUST have at least 1 test"
  - "Edge cases: null, empty, large, concurrent"
validation_checks:
  - coverage_threshold_met
  - all_tests_passing
  - edge_cases_covered
priority: 2
enabled: true
""",
    "security": """
name: security
version: "2.0.0"
description: "Security skill: implement secure coding practices"
category: safety
rules:
  - no_hardcoded_secrets
  - input_validation_required
  - xss_prevention
  - csrf_protection
  - dependency_audit
constraints:
  - "ALL secrets in environment variables"
  - "Parameterized queries ONLY"
  - "NO eval(), NO innerHTML with user data"
validation_checks:
  - no_secrets_in_code
  - input_validation_present
  - security_headers_configured
priority: 1
enabled: true
""",
}
