from flask import Blueprint, render_template, jsonify

error_bp = Blueprint('error', __name__)

@error_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error_code=404, error_message="Page not found"), 404

@error_bp.app_errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal Server Error", "message": str(e)}), 500 