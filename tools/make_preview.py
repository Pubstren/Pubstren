#!/usr/bin/env python3
"""
把 README.md 打包成可以直接双击打开的预览页 preview.html。

用途：在推送到 GitHub 之前，先看看渲染出来什么效果。
GitHub 用的就是标准 GFM，所以这里看到的基本等于实际效果。

    python3 tools/make_preview.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "README.md"
OUT = ROOT / "preview.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pubstren — GitHub 主页预览</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 0 96px; background: #ffffff; color: #1f2328;
    font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
          Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    -webkit-font-smoothing: antialiased;
  }
  .note {
    max-width: 1012px; margin: 0 auto 20px; padding: 0 32px;
    color: #59636e; font-size: 13px;
  }
  .note b { color: #1f2328; font-weight: 500; }
  .wrap { max-width: 1012px; margin: 0 auto; padding: 0 32px; }
  .md { font-size: 16px; line-height: 1.5; }
  .md h2 {
    font-size: 24px; font-weight: 600; margin: 28px 0 16px;
    padding-bottom: .3em; border-bottom: 1px solid #d1d9e0;
  }
  .md p { margin: 0 0 16px; }
  .md hr { height: 1px; margin: 28px 0; background: #d1d9e0; border: 0; }
  .md a { color: #0969da; text-decoration: none; }
  .md a:hover { text-decoration: underline; }
  .md img { max-width: 100%; }
  .md strong { font-weight: 600; }
  .md ul { margin: 0 0 16px; padding-left: 2em; }
  .md li { margin-bottom: 4px; }
  .md details { margin: 0 0 16px; }
  .md summary { cursor: pointer; font-weight: 500; }
  .md sub { font-size: 12px; }
</style>
</head>
<body>
<p class="note">本地预览 · <b>README.md</b> 的 GFM 渲染效果，与 GitHub 实际显示基本一致</p>
<div class="wrap"><div class="md" id="content"></div></div>
<script type="text/markdown" id="src">
__MARKDOWN__
</script>
<script>__MARKED__</script>
<script>
  marked.setOptions({ gfm: true, breaks: false });
  document.getElementById('content').innerHTML =
    marked.parse(document.getElementById('src').textContent);
</script>
</body>
</html>
"""

VENDOR = Path(__file__).resolve().parent / "vendor" / "marked.min.js"
CDN = '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>'


def main() -> None:
    md = SRC.read_text(encoding="utf-8")
    for name, text in (("README.md", md),):
        if "</script" in text.lower():
            raise SystemExit(f"{name} 里出现了 </script，会截断预览页，请先处理")

    # 优先内联本地 vendor 里的 marked，保证离线 / 无代理也能打开
    if VENDOR.exists():
        js = VENDOR.read_text(encoding="utf-8")
        marked_block = js
        print(f"using vendored marked ({len(js)} chars)")
    else:
        marked_block = ""
        print("vendor/marked.min.js 不存在，预览页将回退到 CDN")

    html = TEMPLATE.replace("__MARKDOWN__", md).replace("__MARKED__", marked_block)
    if not marked_block:
        html = html.replace("<script></script>", CDN)

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
