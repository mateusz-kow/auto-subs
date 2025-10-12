from pydantic import BaseModel, Field


class AssStyleSettings(BaseModel):
    """Defines styling for highlighted words in ASS subtitles.

    Note: In this version, the presence of this model enables karaoke timing,
    but custom colors are not yet implemented.
    """


class AssSettings(BaseModel):
    """Defines settings for the generated ASS subtitle file."""

    title: str = "auto-subs generated subtitles"
    play_res_x: int = 1920
    play_res_y: int = 1080
    wrap_style: int = 0
    scaled_border_and_shadow: str = "yes"
    font: str = Field(default="Arial", alias="font_name")
    font_size: int = 48
    primary_color: str = "&H00FFFFFF&"
    secondary_color: str = "&H000000FF&"
    outline_color: str = "&H00000000&"
    back_color: str = "&H00000000&"
    bold: int = 0
    italic: int = 0
    underline: int = 0
    strikeout: int = 0
    scale_x: int = 100
    scale_y: int = 100
    spacing: int = 0
    angle: int = 0
    border_style: int = 1
    outline: int = 2
    shadow: int = 1
    alignment: int = 2
    margin_l: int = 10
    margin_r: int = 10
    margin_v: int = 20
    encoding: int = 1
    highlight_style: AssStyleSettings | None = None

    def to_ass_header(self) -> str:
        """Generates the ASS file header section using the model's settings.

        Returns:
            A string containing the formatted ASS header.
        """
        style_format = (
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
            "Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
            "MarginV, Encoding"
        )
        style_values = (
            f"Style: Default,{self.font},{self.font_size},{self.primary_color},"
            f"{self.secondary_color},{self.outline_color},{self.back_color},"
            f"{self.bold},{self.italic},{self.underline},{self.strikeout},"
            f"{self.scale_x},{self.scale_y},{self.spacing},{self.angle},"
            f"{self.border_style},{self.outline},{self.shadow},{self.alignment},"
            f"{self.margin_l},{self.margin_r},{self.margin_v},{self.encoding}"
        )
        events_format = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"

        return (
            "[Script Info]\n"
            f"Title: {self.title}\n"
            "ScriptType: v4.00+\n"
            "Collisions: Normal\n"
            f"PlayResX: {self.play_res_x}\n"
            f"PlayResY: {self.play_res_y}\n"
            f"WrapStyle: {self.wrap_style}\n"
            f"ScaledBorderAndShadow: {self.scaled_border_and_shadow}\n"
            "\n[V4+ Styles]\n"
            f"{style_format}\n"
            f"{style_values}\n"
            "\n[Events]\n"
            f"{events_format}"
        )
