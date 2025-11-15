from __future__ import annotations

import ast
import math
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, model_validator, validator

Number = Union[int, float]


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


class SafeExpression(BaseModel):
    expr: str

    class Config:
        frozen = True

    @validator("expr")
    def _validate_ast(cls, v: str) -> str:
        try:
            node = ast.parse(v, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"invalid expression syntax: {exc}") from exc
        validator = _SafeAstValidator()
        validator.visit(node)
        return v

    def evaluate(self, context: dict[str, Any] | None = None) -> Number:
        ctx = dict(ALLOWED_MATH_FUNCS)
        if context:
            for k, val in context.items():
                if isinstance(val, (int, float)):
                    ctx[k] = val
        code = compile(ast.parse(self.expr, mode="eval"), "<expr>", "eval")
        return eval(code, {"__builtins__": {}}, ctx)


class _SafeAstValidator(ast.NodeVisitor):
    allowed_nodes = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Num,
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
        ast.IfExp,
        ast.Tuple,
        ast.List,
    }

    allowed_names = set(ALLOWED_MATH_FUNCS.keys())

    def visit(self, node: ast.AST) -> Any:
        if type(node) not in self.allowed_nodes:
            raise ValueError(f"disallowed AST node: {type(node).__name__}")
        return super().visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("only direct function calls allowed")
        func_name = node.func.id
        if func_name not in self.allowed_names:
            raise ValueError(f"function {func_name!r} is not allowed")
        for arg in node.args:
            self.visit(arg)
        for kw in node.keywords:
            self.visit(kw.value)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in self.allowed_names and not node.id.isidentifier():
            raise ValueError(f"identifier {node.id!r} not allowed")
        # names are allowed; evaluation will inject actual context values if provided


ExpressionOrNumber = Union[Number, SafeExpression]


class TransformSchema(BaseModel):
    start: float | None = None
    end: float | None = None
    accel: float | None = None
    ease: Literal["linear", "ease_in", "ease_out", "ease_in_out"] | None = None

    # animated fields (each accepts static number or expression)
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


class ClipSchema(BaseModel):
    vector: str | None = None
    rect: tuple[ExpressionOrNumber, ExpressionOrNumber, ExpressionOrNumber, ExpressionOrNumber] | None = None
    inverse: bool = False


class StyleOverrideSchema(BaseModel):
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

    rotation_x: ExpressionOrNumber | None = None
    rotation_y: ExpressionOrNumber | None = None
    rotation_z: ExpressionOrNumber | None = None

    origin_x: ExpressionOrNumber | None = None
    origin_y: ExpressionOrNumber | None = None

    karaoke: bool | None = None
    clip: ClipSchema | None = None

    transforms: list[TransformSchema] | None = None
    layer: int | None = None
    alignment: int | None = None
    tags: dict[str, Any] | None = None


class EffectSchema(BaseModel):
    name: str
    params: dict[str, Any] | None = None
    transforms: list[TransformSchema] | None = None
    description: str | None = None


class StyleRuleSchema(BaseModel):
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
    effect_params: dict[str, Any] | None = None

    transforms: list[TransformSchema] | None = None


class RuleOperatorSchema(BaseModel):
    target: Literal["char", "word", "syllable", "line"] = "char"

    index: int | None = None
    index_from: int | None = None
    index_to: int | None = None
    index_modulo: int | None = None
    is_first: bool | None = None
    is_last: bool | None = None

    chars: list[str] | None = None
    exclude_chars: list[str] | None = None

    time_from: float | None = None
    time_to: float | None = None

    negate: bool = False

    rules: list[StyleRuleSchema | RuleOperatorSchema] | None = None
    description: str | None = None

    @model_validator(mode="before")
    def _validate_index_range(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("index_from") is not None and values.get("index_to") is not None:
            if values["index_from"] > values["index_to"]:
                raise ValueError("index_from cannot be greater than index_to")
        return values


class KaraokeSyllableSchema(BaseModel):
    text: str
    start: float
    end: float


class KaraokeSettingsSchema(BaseModel):
    type: Literal["word-by-word", "syllable", "mora"] = "word-by-word"
    style_name: str | None = None
    highlight_style: StyleOverrideSchema | None = None
    transition: TransformSchema | None = None


class StylePresetSchema(BaseModel):
    name: str
    override: StyleOverrideSchema


class ScriptInfoSchema(BaseModel):
    Title: str | None = Field(default="auto-subs generated subtitles")
    ScriptType: str | None = Field(default="v4.00+")
    WrapStyle: int | None = 0
    ScaledBorderAndShadow: Literal["yes", "no"] | None = "yes"
    Collisions: Literal["Normal", "Reverse", "Smart", "Force"] | None = "Normal"
    PlayResX: int | None = 1920
    PlayResY: int | None = 1080
    other: dict[str, Any] | None = None


class StyleEngineConfigSchema(BaseModel):
    script_info: ScriptInfoSchema = Field(default_factory=ScriptInfoSchema)
    styles: list[dict[str, Any]] | None = None
    presets: list[StylePresetSchema] | None = None
    rules: list[StyleRuleSchema | RuleOperatorSchema] | None = None
    effects: list[EffectSchema] | None = None
    karaoke: KaraokeSettingsSchema | None = None
    defaults: StyleOverrideSchema | None = None
    metadata: dict[str, Any] | None = None

    @validator("styles", pre=True, each_item=True)
    def _ensure_style_minimal(cls, v: dict[str, Any]) -> dict[str, Any]:
        if "Name" not in v:
            raise ValueError("each style must include a 'Name' field")
        return v


# forward refs
RuleOperatorSchema.update_forward_refs()
StyleRuleSchema.update_forward_refs()
StyleOverrideSchema.update_forward_refs()
TransformSchema.update_forward_refs()
EffectSchema.update_forward_refs()
StyleEngineConfigSchema.update_forward_refs()
SafeExpression.update_forward_refs()
