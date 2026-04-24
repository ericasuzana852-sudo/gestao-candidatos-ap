from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from ..models import SyncLog
from ..converts.sync_service import run_sync

bp = Blueprint("sync", __name__)


@bp.route("/logs")
@login_required
def logs():
    items = SyncLog.query.order_by(SyncLog.started_at.desc()).limit(100).all()
    return render_template("sync/logs.html", logs=items)


@bp.route("/run", methods=["POST"])
@login_required
def run_now():
    if not current_user.is_admin:
        flash("Apenas administradores podem disparar sincronizacao manual.", "danger")
        return redirect(url_for("sync.logs"))
    log = run_sync(triggered_by="manual", user_id=current_user.id)
    if log.status == "success":
        flash(f"Sincronizacao concluida. Encontrados: {log.found}, novos: {log.inserted}, duplicados: {log.duplicates}.", "success")
    else:
        flash(f"Falha na sincronizacao: {log.errors}", "danger")
    return redirect(url_for("sync.logs"))
