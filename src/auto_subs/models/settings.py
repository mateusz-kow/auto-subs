from pydantic import BaseModel, Field


class AssStyleSettings(BaseModel):
    """Defines styling for highlighted words in ASS subtitles."""

    text_color: str = "&H00FFFFFF&"  # Default: White
    border_color: str | None = None
    fade: bool = False


class AssSettings(BaseModel):
    """Defines settings for the generated ASS subtitle file."""

    # [Script Info]
    title: str = "auto-subs generated subtitles"
    play_res_x: int = 1920
    play_res_y: int = 1080
    wrap_style: int = 0
    scaled_border_and_shadow: str = "yes"

    # [V4+ Styles] Default Style
    font: str = Field(default="Arial", alias="font_name")
    font_size: int = 48
    primary_color: str = "&H00FFFFFF&"  # White
    secondary_color: str = "&H000000FF&"  # Red
    outline_color: str = "&H00000000&"  # Black
    back_color: str = "&H00000000&"  # Black (for shadow)
    bold: int = 0  # 0 for false, -1 for true
    italic: int = 0
    underline: int = 0
    strikeout: int = 0
    scale_x: int = 100
    scale_y: int = 100
    spacing: int = 0
    angle: int = 0
    border_style: int = 1  # 1 for outline, 3 for opaque box
    outline: int = 2
    shadow: int = 1
    alignment: int = 2  # 2 for bottom center
    margin_l: int = 10
    margin_r: int = 10
    margin_v: int = 20
    encoding: int = 1  # 1 for UTF-8

    # Custom settings for generation
    highlight_style: AssStyleSettings | None = None

    def to_ass_header(self) -> str:
        """Generates the ASS file header section using the model's settings."""
        return (
            f"[Script Info]\n"
            f"Title: {self.title}\n"
            f"ScriptType: v4.00+\n"
            f"Collisions: Normal\n"
            f"PlayResX: {self.play_res_x}\n"
            f"PlayResY: {self.play_res_y}\n"
            f"WrapStyle: {self.wrap_style}\n"
            f"ScaledBorderAndShadow: {self.scaled_border_and_shadow}\n"
            f"\n[V4+ Styles]\n"
            f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            f"OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            f"ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            f"Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,{self.font},{self.font_size},"
            f"{self.primary_color},{self.secondary_color},"
            f"{self.outline_color},{self.back_color},"
            f"{self.bold},{self.italic},{self.underline},"
            f"{self.strikeout},{self.scale_x},{self.scale_y},"
            f"{self.spacing},{self.angle},{self.border_style},"
            f"{self.outline},{self.shadow},{self.alignment},"
            f"{self.margin_l},{self.margin_r},{self.margin_v},"
            f"{self.encoding}\n"
            f"\n[Events]\n"
            f"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
