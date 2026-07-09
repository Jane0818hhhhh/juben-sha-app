"""从 frontend/static 读取 CSS/JS，生成 static_data.py（内嵌资源）。

EdgeOne 云函数构建器只打包 .py 文件，static/ 下的非 .py 资源不保证被带上，
因此把 CSS/JS 内联进本目录的 static_data.py，由 [[default]].py 的 /static 路由返回，
同时 render_page() 会把它们内联进 HTML，绕过预览链接 eo_token 对独立静态请求的 401 拦截。

用法：在仓库根目录执行  python3.11 cloud-functions/gen_static_data.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT = os.path.join(ROOT, "frontend", "static")
OUT = os.path.join(ROOT, "cloud-functions", "static_data.py")

# 顺序与线上一致
FILES = [
    "css/app.css",
    "js/common.js",
    "js/player.js",
    "js/merchant.js",
    "js/dm.js",
]

HEADER = '''"""内嵌静态资源（CSS/JS）—— 由 gen_static_data.py 自动生成，请勿手改。

EdgeOne 云函数构建器只打包 .py 文件，不保证带上 static/ 下的非 .py 资源，
因此把 CSS/JS 内容内嵌进本文件，由 [[default]].py 的 /static 路由返回。
"""

STATIC_FILES = {
'''


def main():
    parts = [HEADER]
    for rel in FILES:
        path = os.path.join(FRONT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # 防御性：清除任何 U+FFFD 替换字符（历史乱码）
        if "\ufffd" in content:
            raise SystemExit(f"[错误] {rel} 含 U+FFFD 乱码，请先修复源文件再生成")
        parts.append(f"    {rel!r}: {content!r},\n")
    parts.append("}\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"已生成 {OUT}")
    # 自检：能被 import 且键齐全
    ns = {}
    exec(compile(open(OUT, encoding="utf-8").read(), OUT, "exec"), ns)
    keys = list(ns["STATIC_FILES"].keys())
    assert keys == FILES, f"键不一致: {keys}"
    for k in keys:
        print(f"  {k}: {len(ns['STATIC_FILES'][k])} chars")


if __name__ == "__main__":
    main()
