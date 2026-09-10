#!/usr/bin/env python3
"""
生成 GitHub 主页横幅 assets/banner.svg

改这个文件顶部的常量，然后重新运行，就能重做横幅。
只依赖标准库，不需要任何第三方包。

    python3 tools/make_banner.py

原理说明：
  1. GitHub 会剥离 README 里的 <script>/<style>/onclick，
     所以主页上所有动效都只能放在独立 SVG 文件里，用 <img> 引用。
  2. <img> 加载的 SVG 中，CSS 动画与 SMIL 均会正常播放。
     这里用 CSS 动画（比 SMIL 性能好，且每个元素只要一行）。
  3. Chrome / Firefox / Safari 均支持 transform-box: fill-box。
"""

import math
from pathlib import Path

# ---------------------------------------------------------------- 可调参数

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

BG_FROM, BG_TO = "#0D1117", "#111E2B"
INK_FROM, INK_TO = "#FFFFFF", "#79C0FF"
SUB = "#8B949E"
BAR_HI, BAR_LO = "#58A6FF", "#3B82F6"
DOT = "#1C2A3A"

FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"

CYCLE = 8.0               # 蜡烛动画周期（秒）
STAGGER = 0.055           # 逐根延迟（秒）

OUT = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"

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
  .name { animation: rise .9s cubic-bezier(.2,.7,.3,1) .15s both; }
  .sub  { animation: rise .9s cubic-bezier(.2,.7,.3,1) .45s both; }
  @keyframes rise {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .sweep { animation: sw 9s linear 2.5s infinite; }
  @keyframes sw {
    from { transform: translateX(0); }
    to   { transform: translateX(1660px); }
  }
  @media (prefers-reduced-motion: reduce) {
    .b, .sweep, .name, .sub { animation: none; }
  }
"""

# 注意：标题/副标题的 opacity 起点写在 @keyframes 里，配合 fill-mode: both。
# 千万不要在这里单独写 opacity: 0 —— 那样一旦动画不执行，文字就永久不可见。


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


def build() -> str:
    bars = BARS
    peak = round(max(bars) * BAR_SCALE)
    head = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{NAME} — {TAGLINE}">
  <title>{NAME}</title>
  <desc>{TAGLINE}</desc>
  <style>{CORE_CSS}</style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BG_FROM}"/>
      <stop offset="1" stop-color="{BG_TO}"/>
    </linearGradient>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{INK_FROM}"/>
      <stop offset="1" stop-color="{INK_TO}"/>
    </linearGradient>
    <linearGradient id="bar" gradientUnits="userSpaceOnUse" x1="0" y1="{BASE_Y - peak}" x2="0" y2="{BASE_Y}">
      <stop offset="0" stop-color="{BAR_HI}"/>
      <stop offset="1" stop-color="{BAR_LO}" stop-opacity="0.35"/>
    </linearGradient>
    <linearGradient id="sweepG" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#7FC1FF" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#7FC1FF" stop-opacity="0.08"/>
      <stop offset="1" stop-color="#7FC1FF" stop-opacity="0"/>
    </linearGradient>
    <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse">
      <circle cx="1.6" cy="1.6" r="1.2" fill="{DOT}"/>
    </pattern>
    <clipPath id="round">
      <rect x="0" y="0" width="{W}" height="{H}" rx="14"/>
    </clipPath>
  </defs>

  <g clip-path="url(#round)">
    <rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg)"/>
    <rect x="0" y="0" width="{W}" height="{H}" fill="url(#dots)"/>

    <rect class="sweep" x="-460" y="0" width="460" height="{H}" fill="url(#sweepG)"/>

    <text class="name" x="{W / 2}" y="{NAME_Y}" text-anchor="middle" font-family="{FONT}" font-size="{NAME_SIZE}" font-weight="700" letter-spacing="-1" fill="url(#ink)">{NAME}</text>

    <text class="sub" x="{W / 2}" y="{SUB_Y}" text-anchor="middle" font-family="{FONT}" font-size="{SUB_SIZE}" letter-spacing="{SUB_TRACKING}" fill="{SUB}">{TAGLINE}</text>

    <line x1="0" y1="{BASE_Y + 1}" x2="{W}" y2="{BASE_Y + 1}" stroke="{BAR_LO}" stroke-width="1" opacity="0.22"/>

{bars_svg(bars)}
  </g>
</svg>
'''
    return head


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size} bytes, {len(BARS)} bars)")
    print(f"bar range: {min(BARS)} - {max(BARS)}")
