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

    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=160)
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
    title_top = -half_h + 18
    ax.plot([-half_w, half_w], [title_top, title_top], color="black", linewidth=0.8)
    ax.plot([half_w - 70, half_w - 70], [-half_h, title_top], color="black", linewidth=0.8)
    ax.plot([half_w - 115, half_w - 115], [-half_h, title_top], color="black", linewidth=0.8)
    ax.plot([-half_w, half_w], [-half_h + 9, -half_h + 9], color="black", linewidth=0.8)

    ax.plot([-60, 60], [0, 0], color="gray", linestyle="--", linewidth=0.8)
    ax.plot([0, 0], [-30, 30], color="gray", linestyle="--", linewidth=0.8)

    text_kwargs = {"fontproperties": font} if font else {}
    ax.text(-half_w + 4, -half_h + 12, "高程布置图", fontsize=16, **text_kwargs)
    ax.text(-half_w + 4, -half_h + 5.5, "纵向比例尺 1:50", fontsize=9, **text_kwargs)
    ax.text(-half_w + 4, -half_h + 2.0, "横向比例尺 1:500", fontsize=9, **text_kwargs)
    ax.text(-half_w + 4, half_h - 7, "比例控制：H 1:500，V 1:50，纵向放大 10 倍", fontsize=9, **text_kwargs)

    ax.text(half_w - 68, -half_h + 12, "说明", fontsize=11, **text_kwargs)
    ax.text(half_w - 68, -half_h + 7, "1. 本图标高以 m 计，标高为绝对标高。", fontsize=8, **text_kwargs)
    ax.text(
        half_w - 68,
        -half_h + 3,
        "2. 图中污水管、污泥管、回流污泥管及送风管采用不同线型表示。",
        fontsize=7,
        **text_kwargs,
    )
    ax.text(half_w - 113, -half_h + 12, "图例", fontsize=11, **text_kwargs)
    ax.text(half_w - 113, -half_h + 5, "（后续填写管线与构筑物图例）", fontsize=8, **text_kwargs)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render_preview())
