"""剧本杀一站式平台 —— 主应用入口。

一套 Flask 后端服务三端（玩家/店家/DM）+ 响应式 Web 前端。
"""
import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from backend.config import Config
from backend.models import db
from backend.seed import seed_all
from backend.services.llm import llm_status
from backend.routes.player import player_bp
from backend.routes.merchant import merchant_bp
from backend.routes.dm import dm_bp

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
)
app.config.from_object(Config)
CORS(app)

db.init_app(app)
app.register_blueprint(player_bp)
app.register_blueprint(merchant_bp)
app.register_blueprint(dm_bp)


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


def init_db():
    with app.app_context():
        db.create_all()
        seed_all()


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
