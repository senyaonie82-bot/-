"""Render a simple PNG preview for the elevation layout frame."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from cad_config import FRAME_HEIGHT, FRAME_WIDTH


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "output" / "elevation_layout_frame.png"


def _font() -> FontProperties | None:
    candidates = (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    )
    for candidate in candidates:
        if candidate.exists():
            return FontProperties(fname=str(candidate))
    return None


def render_preview(path: Path = OUTPUT_PATH) -> Path:
    font = _font()
    half_w = FRAME_WIDTH / 2
    half_h = FRAME_HEIGHT / 2

    fig, ax = plt.subplots(figsize=(14.1, 10.0), dpi=120)
    ax.set_aspect("equal")
    ax.set_xlim(-half_w - 5, half_w + 5)
    ax.set_ylim(-half_h - 5, half_h + 5)
    ax.axis("off")

    ax.plot(
        [-half_w, half_w, half_w, -half_w, -half_w],
        [-half_h, -half_h, half_h, half_h, -half_h],
        color="black",
        linewidth=1.2,
    )
    title_top = -half_h + 72
    ax.plot([-half_w, half_w], [title_top, title_top], color="black", linewidth=0.8)
    ax.plot([half_w - 330, half_w - 330], [-half_h, title_top], color="black", linewidth=0.8)
    ax.plot([half_w - 500, half_w - 500], [-half_h, title_top], color="black", linewidth=0.8)
    ax.plot([-half_w, half_w], [-half_h + 36, -half_h + 36], color="black", linewidth=0.8)

    ax.plot([-260, 260], [0, 0], color="gray", linestyle="--", linewidth=0.8)
    ax.plot([0, 0], [-130, 130], color="gray", linestyle="--", linewidth=0.8)

    text_kwargs = {"fontproperties": font} if font else {}
    ax.text(-half_w + 18, -half_h + 44, "图名：高程布置图", fontsize=16, **text_kwargs)
    ax.text(-half_w + 18, half_h - 30, "比例控制：H 1:500，V 1:50，纵向放大 10 倍", fontsize=10, **text_kwargs)

    notes_x = half_w - 330 + 10
    ax.text(notes_x, -half_h + 48, "说明：", fontsize=11, **text_kwargs)
    ax.text(notes_x, -half_h + 30, "1. 本图纵向比例尺为 1:50，横向比例尺为 1:500。", fontsize=8, **text_kwargs)
    ax.text(notes_x, -half_h + 16, "2. 本图标高以 m 计，标高为绝对标高。", fontsize=8, **text_kwargs)

    legend_x = half_w - 500 + 10
    ax.text(legend_x, -half_h + 48, "图例", fontsize=11, **text_kwargs)
    legend_items = (
        ("污水管", "solid", 2.0),
        ("污泥管", "dashed", 1.5),
        ("回流污泥管", "dashdot", 1.5),
        ("送风管", (0, (5, 2, 1, 2)), 1.2),
    )
    for index, (label, style, width) in enumerate(legend_items):
        y = -half_h + 32 - index * 8
        ax.plot([legend_x, legend_x + 46], [y, y], color="black", linestyle=style, linewidth=width)
        ax.text(legend_x + 54, y - 2.5, label, fontsize=6, **text_kwargs)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render_preview())
