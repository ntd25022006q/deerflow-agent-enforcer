"""
Unit tests for skill_registry.py — SkillDefinition, SkillRegistry.
All tests use real YAML skill files on disk — zero mocks.
"""

import textwrap
from pathlib import Path

import pytest
import yaml

from deerflow_core.engine.skill_registry import SkillDefinition, SkillRegistry


# ============================================================
# SkillDefinition tests
# ============================================================


class TestSkillDefinition:

    def test_creation_with_required_fields(self):
        s = SkillDefinition(
            name="coding", version="2.0.0",
            description="Write code", category="core",
        )
        assert s.name == "coding"
        assert s.version == "2.0.0"
        assert s.rules == []
        assert s.constraints == []
        assert s.enabled is True
        assert s.priority == 5

    def test_creation_with_all_fields(self):
        s = SkillDefinition(
            name="testing", version="1.0.0",
            description="Write tests", category="quality",
            rules=["rule_a", "rule_b"],
            required_tools=["pytest", "coverage"],
            required_knowledge=["TDD", "BDD"],
            constraints=["constraint_1"],
            validation_checks=["check_1", "check_2"],
            enabled=True, priority=2,
        )
        assert len(s.rules) == 2
        assert len(s.required_tools) == 2
        assert s.priority == 2

    def test_to_dict_roundtrip(self):
        s = SkillDefinition(
            name="security", version="3.0.0",
            description="Security checks", category="safety",
            rules=["no_secrets", "input_validation"],
            constraints=["NO eval()"],
            validation_checks=["secrets_check"],
            required_tools=["scanner"],
            required_knowledge=["OWASP"],
            priority=1,
        )
        d = s.to_dict()
        assert d["name"] == "security"
        assert d["version"] == "3.0.0"
        assert len(d["rules"]) == 2
        assert len(d["constraints"]) == 1
        assert d["enabled"] is True
        assert d["priority"] == 1
        assert "required_tools" in d
        assert "required_knowledge" in d
        assert "validation_checks" in d

    def test_to_dict_has_all_keys(self):
        s = SkillDefinition(name="x", version="1", description="d", category="c")
        d = s.to_dict()
        expected_keys = {
            "name", "version", "description", "category", "rules",
            "required_tools", "required_knowledge", "constraints",
            "validation_checks", "enabled", "priority",
        }
        assert set(d.keys()) == expected_keys


# ============================================================
# SkillRegistry tests — real YAML loading
# ============================================================


class TestSkillRegistry:

    @pytest.fixture
    def registry(self):
        return SkillRegistry(skills_dir="/nonexistent/path")  # Only builtin skills

    def test_builtin_skills_loaded(self, registry):
        assert len(registry.skills) >= 6
        assert "coding" in registry.skills
        assert "testing" in registry.skills
        assert "security" in registry.skills
        assert "architecture" in registry.skills
        assert "documentation" in registry.skills
        assert "deployment" in registry.skills

    def test_coding_skill_has_correct_rules(self, registry):
        coding = registry.skills["coding"]
        assert coding.category == "core"
        assert coding.priority == 1
        assert "strict_typing" in coding.rules
        assert "no_prohibited_patterns" in coding.rules
        assert len(coding.validation_checks) >= 4

    def test_security_skill_has_correct_constraints(self, registry):
        security = registry.skills["security"]
        assert security.priority == 1
        has_no_eval = any("eval" in c.lower() for c in security.constraints)
        assert has_no_eval, "Security skill must mention eval() as forbidden"
        has_env_vars = any("environment" in c.lower() for c in security.constraints)
        assert has_env_vars, "Security skill must require env vars for secrets"

    def test_testing_skill_requirements(self, registry):
        testing = registry.skills["testing"]
        assert testing.category == "quality"
        assert testing.priority == 2
        assert "test_runner" in testing.required_tools
        assert "coverage_tool" in testing.required_tools

    def test_activate_skill_success(self, registry):
        assert registry.activate_skill("coding") is True
        assert "coding" in registry.active_skills

    def test_activate_nonexistent_skill_returns_false(self, registry):
        assert registry.activate_skill("nonexistent_skill") is False
        assert "nonexistent_skill" not in registry.active_skills

    def test_deactivate_skill(self, registry):
        registry.activate_skill("coding")
        assert registry.deactivate_skill("coding") is True
        assert "coding" not in registry.active_skills

    def test_deactivate_non_active_skill_returns_false(self, registry):
        assert registry.deactivate_skill("coding") is False

    def test_get_active_rules_empty(self, registry):
        assert registry.get_active_rules() == []

    def test_get_active_rules_after_activation(self, registry):
        registry.activate_skill("coding")
        registry.activate_skill("security")
        rules = registry.get_active_rules()
        assert "strict_typing" in rules
        assert "no_hardcoded_secrets" in rules

    def test_get_active_constraints(self, registry):
        registry.activate_skill("coding")
        registry.activate_skill("security")
        constraints = registry.get_active_constraints()
        assert any("mock" in c.lower() for c in constraints)
        assert any("eval" in c.lower() for c in constraints)

    def test_get_skill_prompt_empty(self, registry):
        assert registry.get_skill_prompt() == ""

    def test_get_skill_prompt_with_active_skills(self, registry):
        registry.activate_skill("coding")
        prompt = registry.get_skill_prompt()
        assert "<active-skills>" in prompt
        assert "</active-skills>" in prompt
        assert "coding" in prompt
        assert "### Rules:" in prompt
        assert "### Constraints:" in prompt
        assert "### Validation Checks:" in prompt

    def test_get_skill_prompt_sorted_by_priority(self, registry):
        registry.activate_skill("documentation")  # priority 5
        registry.activate_skill("security")       # priority 1
        prompt = registry.get_skill_prompt()
        security_pos = prompt.index("Skill: security")
        doc_pos = prompt.index("Skill: documentation")
        assert security_pos < doc_pos, "Higher priority skills should appear first"

    def test_validate_active_skills(self, registry):
        registry.activate_skill("coding")
        registry.activate_skill("security")
        results = registry.validate_active_skills()
        assert "coding" in results
        assert "security" in results
        assert len(results["coding"]) == 3  # linter, type_checker, formatter

    def test_validate_active_skills_empty(self, registry):
        assert registry.validate_active_skills() == {}

    def test_list_skills_returns_all_sorted(self, registry):
        skills = registry.list_skills()
        assert len(skills) >= 6
        # Should be sorted by priority
        priorities = [s["priority"] for s in skills]
        assert priorities == sorted(priorities)

    def test_list_skills_each_has_dict_keys(self, registry):
        skills = registry.list_skills()
        for s in skills:
            assert "name" in s
            assert "version" in s
            assert "description" in s
            assert "category" in s
            assert "priority" in s

    def test_custom_yaml_skill_loading(self, custom_skill_yaml):
        """Load a real YAML skill file from disk."""
        registry = SkillRegistry(skills_dir=str(custom_skill_yaml.parent))
        # Wait - the custom skill file is in tmp_path which might not be
        # picked up by rglob. Let me verify.
        assert "performance" in registry.skills, (
            "Custom skill from YAML should be loaded"
        )
        perf = registry.skills["performance"]
        assert perf.version == "1.5.0"
        assert "lazy_load_routes" in perf.rules
        assert "Bundle size" in perf.constraints[0]

    def test_custom_skill_can_be_activated(self, custom_skill_yaml):
        registry = SkillRegistry(skills_dir=str(custom_skill_yaml.parent))
        assert registry.activate_skill("performance") is True
        assert "performance" in registry.active_skills

    def test_all_builtin_skills_have_validation_checks(self, registry):
        for name, skill in registry.skills.items():
            assert len(skill.validation_checks) >= 3, (
                f"Skill '{name}' should have at least 3 validation checks"
            )

    def test_all_builtin_skills_have_required_knowledge(self, registry):
        for name, skill in registry.skills.items():
            assert len(skill.required_knowledge) >= 2, (
                f"Skill '{name}' should document required knowledge"
            )
