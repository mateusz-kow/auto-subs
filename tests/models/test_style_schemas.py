import re
from typing import Any

import pytest
from pydantic import ValidationError

from autosubs.models.styles import domain
from autosubs.models.styles.schemas import (
    ClipSchema,
    EffectSchema,
    KaraokeSettingsSchema,
    RuleOperatorSchema,
    SafeExpression,
    ScriptInfoSchema,
    StyleEngineConfigSchema,
    StyleOverrideSchema,
    StylePresetSchema,
    StyleRuleSchema,
    TransformSchema,
)


@pytest.mark.parametrize(
    "expr, context, expected",
    [
        ("1 + 1", None, 2),
        ("x * 2", {"x": 5}, 10),
        ("sin(pi / 2)", None, 1.0),
        ("min(x, y)", {"x": 10, "y": 3}, 3),
        ("x", {"x": 5, "z": "not_a_number"}, 5),
    ],
)
def test_safe_expression_evaluate(expr: str, context: dict[str, Any] | None, expected: float) -> None:
    """Test that SafeExpression evaluates correctly with and without context."""
    safe_expr = SafeExpression(expr=expr)
    assert safe_expr.evaluate(context) == expected


def test_safe_expression_str_and_int() -> None:
    """Test the __str__ and __int__ methods of SafeExpression."""
    safe_expr = SafeExpression(expr="5.5 * 2")
    # Evaluation with no context should work for constants
    assert str(safe_expr) == "11.0"
    assert int(safe_expr) == 11


@pytest.mark.parametrize(
    "bad_expr",
    [
        "__import__('os').system('echo pwned')",
        "open('file.txt')",
        "foo.bar()",
        "lambda: 1",
        "[x for x in [1,2,3]]",
        "a if b else c",
        "some_var",
        "MyClass()",
    ],
)
def test_safe_expression_validator_rejects_unsafe_code(bad_expr: str) -> None:
    """Test that the SafeExpression validator rejects various unsafe expressions."""
    safe_expr = SafeExpression(expr=bad_expr)
    with pytest.raises(ValueError):
        safe_expr.evaluate()


def test_safe_expression_rejects_invalid_syntax() -> None:
    """Test that invalid Python syntax is caught at initialization."""
    with pytest.raises(ValidationError, match="Invalid expression syntax"):
        SafeExpression(expr="import os")


def test_schema_to_domain_conversions() -> None:
    """Test simple schema to domain conversions."""
    clip_domain = ClipSchema(vector="m 0 0 l 10 10").to_domain()
    assert isinstance(clip_domain, domain.Clip)
    assert clip_domain.vector == "m 0 0 l 10 10"

    preset_domain = StylePresetSchema(name="Test", override=StyleOverrideSchema(bold=True)).to_domain()
    assert isinstance(preset_domain, domain.StylePreset)
    assert preset_domain.override.bold is True


def test_style_override_to_domain_with_nested_models() -> None:
    """Test StyleOverrideSchema.to_domain with nested clip and transforms."""
    schema = StyleOverrideSchema(
        clip=ClipSchema(inverse=True), transforms=[TransformSchema(end=100), TransformSchema(start=100, end=200)]
    )
    domain_obj = schema.to_domain()
    assert isinstance(domain_obj.clip, domain.Clip)
    assert domain_obj.clip.inverse is True
    assert isinstance(domain_obj.transforms, list)
    assert len(domain_obj.transforms) == 2
    assert isinstance(domain_obj.transforms[0], domain.Transform)


def test_effect_schema_to_domain() -> None:
    """Test EffectSchema.to_domain with nested transforms."""
    schema = EffectSchema(name="FadeIn", transforms=[TransformSchema(end=500, alpha=0)])
    domain_obj = schema.to_domain()
    assert isinstance(domain_obj, domain.Effect)
    assert isinstance(domain_obj.transforms, list)
    assert len(domain_obj.transforms) == 1
    assert isinstance(domain_obj.transforms[0], domain.Transform)


def test_rule_operator_validate_index_range() -> None:
    """Test that RuleOperatorSchema validates the index range."""
    with pytest.raises(ValidationError, match="index_from cannot be greater than index_to"):
        RuleOperatorSchema(index_from=10, index_to=5)
    # Should not raise
    RuleOperatorSchema(index_from=5, index_to=10)


def test_rule_operator_to_domain() -> None:
    """Test RuleOperatorSchema.to_domain conversion."""
    schema = RuleOperatorSchema(
        regex="^A",
        exclude_regex="B$",
        rules=[RuleOperatorSchema(target="char", is_first=True)],
    )
    domain_obj = schema.to_domain()
    assert isinstance(domain_obj, domain.RuleOperator)
    assert isinstance(domain_obj.regex, re.Pattern)
    assert isinstance(domain_obj.exclude_regex, re.Pattern)
    assert isinstance(domain_obj.rules, list)
    assert isinstance(domain_obj.rules[0], domain.RuleOperator)


def test_style_rule_to_domain() -> None:
    """Test StyleRuleSchema.to_domain conversion."""
    schema = StyleRuleSchema(pattern=r"\w+", regex="^A", exclude_regex="B$")
    domain_obj = schema.to_domain()
    assert isinstance(domain_obj.pattern, re.Pattern)
    assert isinstance(domain_obj.regex, re.Pattern)
    assert isinstance(domain_obj.exclude_regex, re.Pattern)


def test_karaoke_settings_to_domain() -> None:
    """Test KaraokeSettingsSchema.to_domain conversion with nested models."""
    schema = KaraokeSettingsSchema(highlight_style=StyleOverrideSchema(bold=True), transition=TransformSchema(end=100))
    domain_obj = schema.to_domain()
    assert isinstance(domain_obj.highlight_style, domain.StyleOverride)
    assert isinstance(domain_obj.transition, domain.Transform)


def test_script_info_to_dict() -> None:
    """Test ScriptInfoSchema.to_dict with and without 'other' data."""
    schema = ScriptInfoSchema(Title="Test", other={"CustomField": "Value"})
    data = schema.to_dict()
    assert data["Title"] == "Test"
    assert data["CustomField"] == "Value"
    assert "other" not in data


def test_style_engine_config_validator() -> None:
    """Test the 'styles' field validator in StyleEngineConfigSchema."""
    with pytest.raises(ValidationError, match="Each style must include a 'Name' field"):
        StyleEngineConfigSchema(styles=[{"Fontname": "Arial"}])

    # Should not raise for None or valid style
    StyleEngineConfigSchema(styles=None)
    StyleEngineConfigSchema(styles=[{"Name": "Default"}])
