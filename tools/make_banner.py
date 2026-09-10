#!/usr/bin/env python3
"""
生成 GitHub 主页横幅 assets/banner.svg

    python3 tools/make_banner.py                 # 用默认主题
    python3 tools/make_banner.py -t navy         # 换主题
    python3 tools/make_banner.py --list          # 看所有主题
    python3 tools/make_banner.py -t paper -o /tmp/x.svg

只依赖标准库。想加新配色，往 THEMES 里加一项就行。

原理说明：
  1. GitHub 会剥离 README 里的 <script>/<style>/onclick，
     所以主页上所有动效都只能放在独立 SVG 文件里，用 <img> 引用。
  2. <img> 加载的 SVG 中，CSS 动画会正常播放（SMIL 较不可靠，不用）。
  3. Chrome / Firefox / Safari 均支持 transform-box: fill-box。
"""

import argparse
from pathlib import Path

# ---------------------------------------------------------------- 文案与形态

NAME = "Pubstren"
TAGLINE = "Quantitative Research · Data Infrastructure"

# 蜡烛高度，从左到右。手写而非公式生成 —— 公式出来的太像波形，不像数据。
BARS = [28, 34, 29, 41, 37, 46, 39, 33, 44, 52, 45, 38,
        50, 58, 52, 64, 60, 71, 66, 58, 73, 81, 70, 62,
        55, 66, 76, 68, 60, 72, 83, 77, 88, 81, 73, 85,
        92, 85, 77, 89, 81, 70, 79, 87, 75, 83, 91, 88, 78, 86]

W, H = 1200, 330          # 画布尺寸
BASE_Y = 310              # 蜡烛基准线
BAR_W = 10                # 蜡烛宽度
BAR_SCALE = 1.25          # 蜡烛整体高度系数
NAME_SIZE, SUB_SIZE = 62, 24
NAME_Y, SUB_Y = 105, 167
SUB_TRACKING = 0.5        # 副标题字距（英文不需要中文那么宽）
RADIUS = 14               # 圆角

FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"

CYCLE = 8.0               # 蜡烛动画周期（秒）
STAGGER = 0.055           # 逐根延迟（秒）

# ---------------------------------------------------------------- 主题配色
# bg_from/bg_to 底色渐变；ink_from/ink_to 主标题渐变；sub 副标题
# bar_hi/bar_lo 蜡烛高/低色；dot 背景点阵；sweep 扫光；border 描边（None 不加）

THEMES = {
    "dark": {
        "label": "GitHub 暗色（默认）",
        "bg_from": "#0D1117", "bg_to": "#111E2B",
        "ink_from": "#FFFFFF", "ink_to": "#79C0FF",
        "sub": "#8B949E",
        "bar_hi": "#58A6FF", "bar_lo": "#3B82F6",
        "dot": "#1C2A3A", "sweep": "#7FC1FF", "border": None,
    },
    "navy": {
        "label": "深海蓝",
        "bg_from": "#071A2F", "bg_to": "#0E3055",
        "ink_from": "#FFFFFF", "ink_to": "#7DD3FC",
        "sub": "#93A6BC",
        "bar_hi": "#38BDF8", "bar_lo": "#0369A1",
        "dot": "#12405F", "sweep": "#8BD8FF", "border": None,
    },
    "violet": {
        "label": "紫罗兰",
        "bg_from": "#130F22", "bg_to": "#241A38",
        "ink_from": "#FFFFFF", "ink_to": "#C4B5FD",
        "sub": "#A5A0B8",
        "bar_hi": "#A78BFA", "bar_lo": "#6D28D9",
        "dot": "#2E2348", "sweep": "#C9B8FF", "border": None,
    },
    "paper": {
        "label": "纸白（浅色）",
        "bg_from": "#FFFFFF", "bg_to": "#EEF2F7",
        "ink_from": "#1F2328", "ink_to": "#0969DA",
        "sub": "#59636E",
        "bar_hi": "#2D7FF9", "bar_lo": "#79B8FF",
        "dot": "#DCE3EA", "sweep": "#0969DA", "border": "#D0D7DE",
    },
}

DEFAULT_THEME = "violet"

# CSS 单独放，避免和 f-string 的花括号打架
# 全部用 CSS 动画而不用 SMIL：SVG 通过 <img> 加载时，SMIL 的 fill="freeze"
# 在部分浏览器 / 截图环境下不可靠，CSS 动画则稳定生效。
CORE_CSS = """
  .b {
    transform-box: fill-box;
    transform-origin: 50% 100%;
    animation: grow 8s cubic-bezier(.4,0,.25,1) infinite;
  }
  @keyframes grow {
    0%   { transform: scaleY(0); }
    10%  { transform: scaleY(1); }
    86%  { transform: scaleY(1); }
    100% { transform: scaleY(0); }
  }
  .sweep { animation: sw 9s linear 2.5s infinite; }
  @keyframes sw {
    from { transform: translateX(0); }
    to   { transform: translateX(1660px); }
  }
  @media (prefers-reduced-motion: reduce) {
    .b, .sweep { animation: none; }
  }
"""

# 关于文字的入场动画：**故意不做**。
# 试过两种写法，都出过「文字整段消失」的事故：
#   a) 静态 opacity: 0 + 入场动画 —— 动画不执行就永久不可见；
#   b) @keyframes from{opacity:0} + fill-mode: both —— 只在浏览器完全不支持动画时降级；
#      一旦动画启动了但没推进（<img> 内的虚拟时间 / 后台标签页等），
#      它会停在 from 帧，文字照样不可见。
# 结论：文字是信息主体，可见性不能拿去赌动画执行。只让装饰元素（蜡烛、扫光）动。
# 如果确实想要文字进场效果，只用 transform，不要碰 opacity。

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"


# ---------------------------------------------------------------- 生成逻辑

def bars_svg(bars: list[int]) -> str:
    n = len(bars)
    hs = [round(h * BAR_SCALE) for h in bars]
    step = (W - BAR_W * 2) / (n - 1)
    rows = []
    for i, h in enumerate(hs):
        x = BAR_W / 2 + i * step
        y = BASE_Y - h
        rows.append(
            f'    <rect class="b" x="{x:.1f}" y="{y}" width="{BAR_W}" height="{h}"'
            f' rx="2" fill="url(#bar)" style="animation-delay:{i * STAGGER:.3f}s"/>'
        )
    return "\n".join(rows)


def build(theme: str = DEFAULT_THEME) -> str:
    t = THEMES[theme]
    peak = round(max(BARS) * BAR_SCALE)

    border = ""
    if t["border"]:
        border = (f'\n    <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"'
                  f' rx="{RADIUS}" fill="none" stroke="{t["border"]}" stroke-width="1"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{NAME} — {TAGLINE}">
  <title>{NAME}</title>
  <desc>{TAGLINE}</desc>
  <style>{CORE_CSS}</style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t["bg_from"]}"/>
      <stop offset="1" stop-color="{t["bg_to"]}"/>
    </linearGradient>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t["ink_from"]}"/>
      <stop offset="1" stop-color="{t["ink_to"]}"/>
    </linearGradient>
    <linearGradient id="bar" gradientUnits="userSpaceOnUse" x1="0" y1="{BASE_Y - peak}" x2="0" y2="{BASE_Y}">
      <stop offset="0" stop-color="{t["bar_hi"]}"/>
      <stop offset="1" stop-color="{t["bar_lo"]}" stop-opacity="0.35"/>
    </linearGradient>
    <linearGradient id="sweepG" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t["sweep"]}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{t["sweep"]}" stop-opacity="0.08"/>
      <stop offset="1" stop-color="{t["sweep"]}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse">
      <circle cx="1.6" cy="1.6" r="1.2" fill="{t["dot"]}"/>
    </pattern>
    <clipPath id="round">
      <rect x="0" y="0" width="{W}" height="{H}" rx="{RADIUS}"/>
    </clipPath>
  </defs>

  <g clip-path="url(#round)">
    <rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg)"/>
    <rect x="0" y="0" width="{W}" height="{H}" fill="url(#dots)"/>

    <rect class="sweep" x="-460" y="0" width="460" height="{H}" fill="url(#sweepG)"/>

    <text class="name" x="{W / 2}" y="{NAME_Y}" text-anchor="middle" font-family="{FONT}" font-size="{NAME_SIZE}" font-weight="700" letter-spacing="-1" fill="url(#ink)">{NAME}</text>

    <text class="sub" x="{W / 2}" y="{SUB_Y}" text-anchor="middle" font-family="{FONT}" font-size="{SUB_SIZE}" letter-spacing="{SUB_TRACKING}" fill="{t["sub"]}">{TAGLINE}</text>

    <line x1="0" y1="{BASE_Y + 1}" x2="{W}" y2="{BASE_Y + 1}" stroke="{t["bar_lo"]}" stroke-width="1" opacity="0.22"/>

{bars_svg(BARS)}{border}
  </g>
</svg>
'''


def main() -> None:
    ap = argparse.ArgumentParser(description="生成 GitHub 主页横幅 SVG")
    ap.add_argument("-t", "--theme", default=DEFAULT_THEME, choices=sorted(THEMES),
                    help="配色主题")
    ap.add_argument("-o", "--out", default=str(DEFAULT_OUT), help="输出路径")
    ap.add_argument("-l", "--list", action="store_true", help="列出所有主题")
    args = ap.parse_args()

    if args.list:
        for key in sorted(THEMES):
            print(f"  {key:8s} {THEMES[key]['label']}")
        return

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(args.theme), encoding="utf-8")
    print(f"wrote {out}  theme={args.theme}  {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
