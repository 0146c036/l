from flask import Blueprint

# 建立一個獨立的路由藍圖，完全隔絕主程式的語法干擾
render_bp = Blueprint('render_routes', __name__)

@render_bp.route("/", methods=["GET", "HEAD"])
def index():
    return "Hello, Meeting Reminder System is running!", 200

@render_bp.route("/callback", methods=["POST"])
def callback():
    return "OK", 200
