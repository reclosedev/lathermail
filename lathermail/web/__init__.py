import os

from flask import send_from_directory, Blueprint

static_bp = Blueprint('static', __name__)
_static_dir = os.path.join(os.path.dirname(__file__), 'static')


@static_bp.route('/')
def index():
    return send_from_directory(_static_dir, "index.html")


@static_bp.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(_static_dir, filename)
