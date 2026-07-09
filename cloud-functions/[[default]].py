"""剧本杀一站式平台 —— EdgeOne Makers Serverless 入口。

文件名 [[default]].py 是 EdgeOne Pages 的 catch-all 动态路由语法，映射
example.com/* 全部路径。EdgeOne 运行时会直接把本文件中的 `app`（Flask/WSGI
实例）作为应用接管请求，因此：
1. 不写 if __name__ == '__main__' + app.run()（Serverless 不需要常驻进程）；
2. 模板不从磁盘 templates/ 加载，改用 templates_data.py 内嵌字典（DictLoader），
   静态资源 CSS/JS 也从 static_data.py 内嵌字典经 /static 路由返回——因为
   EdgeOne 的 Python 构建器只打包 .py 及其 import 到的模块，不保证带上非 .py
   静态资源，内嵌可从根本上摆脱对外部文件系统结构的依赖；
3. 数据库落到 /tmp（Serverless 唯一可写目录），模块加载时冷启动建表+种子数据。

复用仓库根目录 backend/ 里的全部业务代码（models/routes/services/seed），
本文件只做"装配 + 适配"，业务逻辑零改动。

北极星·炼术师 队伍作品（剧本杀垂直社交平台）
"""
import os
from flask import Flask, render_template, jsonify, Response, abort
from flask_cors import CORS
from jinja2 import DictLoader

from backend.config import Config
from backend.models import db
from backend.seed import seed_all
from backend.services.llm import llm_status
from backend.routes.player import player_bp
from backend.routes.merchant import merchant_bp
from backend.routes.dm import dm_bp

from templates_data import TEMPLATES
from static_data import STATIC_FILES

# static_folder=None：禁用 Flask 内建的磁盘 /static 端点，
# 改由下方自定义路由从内嵌 STATIC_FILES 字典返回，避免端点冲突。
app = Flask(__name__, static_folder=None)
app.config.from_object(Config)
CORS(app)

# 用内嵌字典模板替代磁盘 templates/ 目录
app.jinja_loader = DictLoader(TEMPLATES)

db.init_app(app)
app.register_blueprint(player_bp)
app.register_blueprint(merchant_bp)
app.register_blueprint(dm_bp)


# ---------------- 冷启动初始化数据库 ----------------
_DB_READY = False


def _ensure_db():
    """首次请求前建表 + 灌种子数据。Serverless 冷启动会重跑，幂等。"""
    global _DB_READY
    if _DB_READY:
        return
    with app.app_context():
        db.create_all()
        try:
            seed_all()
        except Exception as e:
            print("[init] seed failed:", e)
    _DB_READY = True


@app.before_request
def _before():
    _ensure_db()


# ---------------- 内嵌静态资源路由 ----------------
_MIME = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


@app.route("/static/<path:filename>")
def static_file(filename):
    content = STATIC_FILES.get(filename)
    if content is None:
        abort(404)
    ext = os.path.splitext(filename)[1]
    mime = _MIME.get(ext, "text/plain; charset=utf-8")
    resp = Response(content, content_type=mime)
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


# ---------------- 页面路由 ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/player")
def player_app():
    return render_template("player.html")


@app.route("/merchant")
def merchant_app():
    return render_template("merchant.html")


@app.route("/dm")
def dm_app():
    return render_template("dm.html")


# ---------------- 系统信息 ----------------
@app.route("/api/system/info")
def system_info():
    st = llm_status()
    return jsonify({
        "app": "剧本杀一站式平台",
        "llm_ready": st["ready"],
        "llm_mode": "real" if st["ready"] else "fallback",
        "model": st["model"],
    })


# ---------------- 诊断接口（排查部署问题用，稳定后可删） ----------------
@app.route("/api/debug/status")
def debug_status():
    import sys
    env_keys = ["LLM_PROVIDER", "OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_DEPLOYMENT",
                "LLM_MODEL", "DATABASE_URL", "TENCENT_SEARCH_SID"]
    env_status = {}
    for k in env_keys:
        v = os.environ.get(k, "")
        # 敏感值只显示长度，不回显明文
        env_status[k] = f"已设置({len(v)}字符)" if v else "未设置"
    st = llm_status()
    # 探测数据库连通性 + 基本计数
    db_info = {}
    try:
        from backend.models import Script, GameSession
        with app.app_context():
            _ensure_db()
            db_info = {
                "uri_scheme": Config.SQLALCHEMY_DATABASE_URI.split(":", 1)[0],
                "scripts": Script.query.count(),
                "sessions": GameSession.query.count(),
            }
    except Exception as e:
        db_info = {"error": str(e)}
    return jsonify({
        "python_version": sys.version,
        "llm_ready": st["ready"],
        "llm_model": st["model"],
        "env_vars": env_status,
        "db": db_info,
    })


@app.errorhandler(Exception)
def handle_any_error(e):
    """把真实报错堆栈返回，方便线上排障（Demo 阶段用）。"""
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    import traceback
    return jsonify({
        "success": False,
        "error": str(e),
        "error_type": type(e).__name__,
        "traceback": traceback.format_exc(),
    }), 500


# 注意：EdgeOne Serverless 运行时直接使用本文件的 `app`（WSGI 实例），
# 不写 app.run()。
