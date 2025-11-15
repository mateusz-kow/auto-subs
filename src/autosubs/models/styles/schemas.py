from __future__ import annotations

import ast
import math
import re
from typing import Literal, cast

from pydantic import BaseModel, Field, field_validator, model_validator

from . import domain

Number = int | float

ALLOWED_MATH_FUNCS = {
    name: getattr(math, name)
    for name in (
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "atan2",
        "sinh",
        "cosh",
        "tanh",
        "asinh",
        "acosh",
        "atanh",
        "sqrt",
        "exp",
        "log",
        "log10",
        "log2",
        "floor",
        "ceil",
        "fabs",
        "pow",
        "degrees",
        "radians",
        "hypot",
    )
}
ALLOWED_MATH_FUNCS.update({"min": min, "max": max, "abs": abs, "round": round})
ALLOWED_CONSTANTS = {"pi": math.pi, "e": math.e}


class _SafeAstValidator(ast.NodeVisitor):
    allowed_nodes = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.FloorDiv,
        ast.LShift,
        ast.RShift,
        ast.BitOr,
        ast.BitAnd,
        ast.BitXor,
        ast.And,
        ast.Or,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Tuple,
        ast.List,
    }
    allowed_names = set(ALLOWED_MATH_FUNCS.keys()) | set(ALLOWED_CONSTANTS.keys())

    def __init__(self, context_keys: set[str] | None = None):
        self.allowed_names.update(context_keys or set())

    def visit(self, node: ast.AST) -> None:
        if type(node) not in self.allowed_nodes:
            raise ValueError(f"Disallowed AST node: {type(node).__name__}")
        super().visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are allowed.")
        if node.func.id not in self.allowed_names:
            raise ValueError(f"Function '{node.func.id}' is not allowed.")
        for arg in node.args:
            self.visit(arg)
        for kw in node.keywords:
            self.visit(kw.value)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in self.allowed_names:
            raise ValueError(f"Identifier '{node.id}' is not in the list of allowed names.")


class SafeExpression(BaseModel):
    """Represents a mathematical expression that can be safely evaluated."""

    model_config = {"frozen": True}
    expr: str

    @field_validator("expr")
    @classmethod
    def validate_expr_syntax(cls, v: str) -> str:
        """Validates that the expression has valid Python syntax."""
        try:
            ast.parse(v, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}") from e
        return v

    def evaluate(self, context: dict[str, object] | None = None) -> Number:
        """Evaluates the expression with a given context."""
        ctx = dict(ALLOWED_MATH_FUNCS)
        ctx.update(ALLOWED_CONSTANTS)
        safe_context: dict[str, object] = {}
        if context:
            safe_context = {k: val for k, val in context.items() if isinstance(val, (int, float))}
            ctx.update(safe_context)

        node = ast.parse(self.expr, mode="eval")
        validator = _SafeAstValidator(context_keys=set(safe_context.keys()))
        validator.visit(node)

        code = compile(node, "<expr>", "eval")
        return cast(Number, eval(code, {"__builtins__": {}}, ctx))

    def __str__(self) -> str:
        """Returns string representation od the object."""
        return str(self.evaluate())

    def __int__(self) -> int:
        """Returns integer representation od the object."""
        return int(self.evaluate())


ExpressionOrNumber = Number | SafeExpression


class TransformSchema(BaseModel):
    """Schema for a single animation or transformation effect."""

    start: float | None = None
    end: float | None = None
    accel: float | None = None
    ease: Literal["linear", "ease_in", "ease_out", "ease_in_out"] | None = None
    font_size: ExpressionOrNumber | None = None
    scale_x: ExpressionOrNumber | None = None
    scale_y: ExpressionOrNumber | None = None
    rotation_x: ExpressionOrNumber | None = None
    rotation_y: ExpressionOrNumber | None = None
    rotation_z: ExpressionOrNumber | None = None
    alpha: ExpressionOrNumber | None = None
    position_x: ExpressionOrNumber | None = None
    position_y: ExpressionOrNumber | None = None
    blur: ExpressionOrNumber | None = None
    border: ExpressionOrNumber | None = None
    shadow: ExpressionOrNumber | None = None
    move_x1: ExpressionOrNumber | None = None
    move_y1: ExpressionOrNumber | None = None
    move_x2: ExpressionOrNumber | None = None
    move_y2: ExpressionOrNumber | None = None
    move_t1: ExpressionOrNumber | None = None
    move_t2: ExpressionOrNumber | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    outline_color: str | None = None
    shadow_color: str | None = None

    def to_domain(self) -> domain.Transform:
        """Converts the schema to its corresponding domain model."""
        return domain.Transform(**self.model_dump())


class ClipSchema(BaseModel):
    """Schema for a vector clipping effect."""

    vector: str | None = None
    rect: tuple[ExpressionOrNumber, ExpressionOrNumber, ExpressionOrNumber, ExpressionOrNumber] | None = None
    inverse: bool = False

    def to_domain(self) -> domain.Clip:
        """Converts the schema to its corresponding domain model."""
        return domain.Clip(**self.model_dump())


class StyleOverrideSchema(BaseModel):
    """Schema for a set of style properties that can override a base style."""

    font_name: str | None = None
    font_size: ExpressionOrNumber | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikeout: bool | None = None
    spacing: ExpressionOrNumber | None = None
    angle: ExpressionOrNumber | None = None
    scale_x: ExpressionOrNumber | None = None
    scale_y: ExpressionOrNumber | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    outline_color: str | None = None
    shadow_color: str | None = None
    alpha: str | ExpressionOrNumber | None = None
    border: ExpressionOrNumber | None = None
    shadow: ExpressionOrNumber | None = None
    blur: ExpressionOrNumber | None = None
    position_x: ExpressionOrNumber | None = None
    position_y: ExpressionOrNumber | None = None
    move_x1: ExpressionOrNumber | None = None
    move_y1: ExpressionOrNumber | None = None
    move_x2: ExpressionOrNumber | None = None
    move_y2: ExpressionOrNumber | None = None
    move_t1: ExpressionOrNumber | None = None
    move_t2: ExpressionOrNumber | None = None
    origin_x: ExpressionOrNumber | None = None
    origin_y: ExpressionOrNumber | None = None
    rotation_x: ExpressionOrNumber | None = None
    rotation_y: ExpressionOrNumber | None = None
    rotation_z: ExpressionOrNumber | None = None
    karaoke: bool | None = None
    clip: ClipSchema | None = None
    transforms: list[TransformSchema] | None = None
    layer: int | None = None
    alignment: int | None = None
    tags: dict[str, object] | None = None

    def to_domain(self) -> domain.StyleOverride:
        """Converts the schema to its corresponding domain model."""
        dump = self.model_dump()
        if self.clip:
            dump["clip"] = self.clip.to_domain()
        if self.transforms:
            dump["transforms"] = [t.to_domain() for t in self.transforms]
        return domain.StyleOverride(**dump)


class EffectSchema(BaseModel):
    """Schema for a named, reusable effect."""

    name: str
    params: dict[str, object] | None = None
    transforms: list[TransformSchema] | None = None
    description: str | None = None

    def to_domain(self) -> domain.Effect:
        """Converts the schema to its corresponding domain model."""
        dump = self.model_dump()
        if self.transforms:
            dump["transforms"] = [t.to_domain() for t in self.transforms]
        return domain.Effect(**dump)


class RuleOperatorSchema(BaseModel):
    """Schema for a condition within a style rule."""

    target: Literal["char", "word", "syllable", "line"] = "char"
    index: int | None = None
    index_from: int | None = None
    index_to: int | None = None
    index_modulo: int | None = None
    is_first: bool | None = None
    is_last: bool | None = None
    chars: list[str] | None = None
    exclude_chars: list[str] | None = None
    regex: str | None = None
    exclude_regex: str | None = None
    time_from: float | None = None
    time_to: float | None = None
    negate: bool = False
    rules: list[StyleRuleSchema | RuleOperatorSchema] | None = None
    transforms: list[TransformSchema] | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_index_range(self) -> RuleOperatorSchema:
        """Validates that index_from is not greater than index_to."""
        if self.index_from is not None and self.index_to is not None and self.index_from > self.index_to:
            raise ValueError("index_from cannot be greater than index_to")
        return self

    def to_domain(self) -> domain.RuleOperator:
        """Converts the schema to its corresponding domain model."""
        dump = self.model_dump()
        if self.rules:
            dump["rules"] = [r.to_domain() for r in self.rules]
        if self.transforms:
            dump["transforms"] = [t.to_domain() for t in self.transforms]
        if self.regex:
            dump["regex"] = re.compile(self.regex)
        if self.exclude_regex:
            dump["exclude_regex"] = re.compile(self.exclude_regex)
        return domain.RuleOperator(**dump)


class StyleRuleSchema(BaseModel):
    """Schema for a rule that applies styles or effects based on conditions."""

    name: str | None = None
    priority: int = 0
    pattern: str | None = None
    apply_to: Literal["line", "word", "char", "syllable"] = "char"
    time_from: float | None = None
    time_to: float | None = None
    speaker: str | None = None
    layer: int | None = None
    style_name: str | None = None
    style_override: StyleOverrideSchema | None = None
    effect: str | None = None
    effect_params: dict[str, object] | None = None
    transforms: list[TransformSchema] | None = None
    regex: str | None = None
    exclude_regex: str | None = None
    operators: list[RuleOperatorSchema] | None = None

    def to_domain(self) -> domain.StyleRule:
        """Converts the schema to its corresponding domain model."""
        dump = self.model_dump()
        if self.style_override:
            dump["style_override"] = self.style_override.to_domain()
        if self.transforms:
            dump["transforms"] = [t.to_domain() for t in self.transforms]
        if self.operators:
            dump["operators"] = [op.to_domain() for op in self.operators]
        if self.pattern:
            dump["pattern"] = re.compile(self.pattern)
        if self.regex:
            dump["regex"] = re.compile(self.regex)
        if self.exclude_regex:
            dump["exclude_regex"] = re.compile(self.exclude_regex)
        return domain.StyleRule(**dump)


class KaraokeSyllableSchema(BaseModel):
    """Schema for a single syllable in karaoke timing."""

    text: str
    start: float
    end: float


class KaraokeSettingsSchema(BaseModel):
    """Schema for karaoke-specific styling settings."""

    type: Literal["word-by-word", "syllable", "mora"] = "word-by-word"
    style_name: str | None = None
    highlight_style: StyleOverrideSchema | None = None
    transition: TransformSchema | None = None

    def to_domain(self) -> domain.KaraokeSettings:
        """Converts the schema to its corresponding domain model."""
        dump = self.model_dump()
        if self.highlight_style:
            dump["highlight_style"] = self.highlight_style.to_domain()
        if self.transition:
            dump["transition"] = self.transition.to_domain()
        return domain.KaraokeSettings(**dump)


class StylePresetSchema(BaseModel):
    """Schema for a named, reusable set of style overrides."""

    name: str
    override: StyleOverrideSchema

    def to_domain(self) -> domain.StylePreset:
        """Converts the schema to its corresponding domain model."""
        return domain.StylePreset(name=self.name, override=self.override.to_domain())


class ScriptInfoSchema(BaseModel):
    """Schema for the [Script Info] section of an ASS file."""

    Title: str | None = Field(default="auto-subs generated subtitles")
    ScriptType: str | None = Field(default="v4.00+")
    WrapStyle: int | None = 0
    ScaledBorderAndShadow: Literal["yes", "no"] | None = "yes"
    Collisions: Literal["Normal", "Reverse", "Smart", "Force"] | None = "Normal"
    PlayResX: int | None = 1920
    PlayResY: int | None = 1080
    other: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        """Converts the script info to a dictionary for ASS generation."""
        data = self.model_dump(exclude_none=True)
        other_data = data.pop("other", None)
        if other_data is not None:
            data.update(other_data)
        return data


class StyleEngineConfigSchema(BaseModel):
    """Schema for the complete style engine configuration."""

    script_info: ScriptInfoSchema = Field(default_factory=ScriptInfoSchema)
    styles: list[dict[str, object]] | None = None
    presets: list[StylePresetSchema] | None = None
    rules: list[StyleRuleSchema | RuleOperatorSchema] | None = None
    effects: list[EffectSchema] | None = None
    karaoke: KaraokeSettingsSchema | None = None
    defaults: StyleOverrideSchema | None = None
    metadata: dict[str, object] | None = None

    @field_validator("styles", mode="before")
    @classmethod
    def ensure_style_name(cls, v: list[dict[str, object]] | None) -> list[dict[str, object]] | None:
        """Validates that each style dictionary has a 'Name' field."""
        if v is None:
            return None
        for item in v:
            if "Name" not in item:
                raise ValueError("Each style must include a 'Name' field.")
        return v

    def to_domain(self) -> domain.StyleEngineConfig:
        """Converts the schema to its corresponding domain model."""
        domain_effects = [e.to_domain() for e in self.effects] if self.effects else []
        effects_map = {e.name: e for e in domain_effects}
        return domain.StyleEngineConfig(
            script_info=self.script_info.to_dict(),
            styles=self.styles or [],
            presets=[p.to_domain() for p in self.presets] if self.presets else [],
            rules=[r.to_domain() for r in self.rules] if self.rules else [],
            effects=effects_map,
            karaoke=self.karaoke.to_domain() if self.karaoke else None,
            defaults=self.defaults.to_domain() if self.defaults else None,
            metadata=self.metadata,
        )


RuleOperatorSchema.model_rebuild()
StyleRuleSchema.model_rebuild()
StyleOverrideSchema.model_rebuild()
TransformSchema.model_rebuild()
EffectSchema.model_rebuild()
StyleEngineConfigSchema.model_rebuild()
SafeExpression.model_rebuild()
