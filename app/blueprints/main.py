from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint("main", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("candidates.list_candidates"))
