from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..models import User, Store

bp = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


@bp.route("/usuarios")
@admin_required
def list_users():
    users = User.query.order_by(User.name).all()
    return render_template("admin/users.html", users=users)


@bp.route("/usuarios/novo", methods=["GET", "POST"])
@admin_required
def new_user():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            flash("E-mail ja cadastrado.", "warning")
            return redirect(url_for("admin.new_user"))
        u = User(
            name=request.form["name"].strip(),
            email=email,
            role=request.form.get("role", "operacional"),
            active=bool(request.form.get("active")),
        )
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.commit()
        flash("Usuario criado.", "success")
        return redirect(url_for("admin.list_users"))
    return render_template("admin/user_form.html", user=None)


@bp.route("/usuarios/<int:uid>/editar", methods=["GET", "POST"])
@admin_required
def edit_user(uid):
    u = User.query.get_or_404(uid)
    if request.method == "POST":
        u.name = request.form["name"].strip()
        u.email = request.form["email"].strip().lower()
        u.role = request.form.get("role", u.role)
        u.active = bool(request.form.get("active"))
        if request.form.get("password"):
            u.set_password(request.form["password"])
        db.session.commit()
        flash("Usuario atualizado.", "success")
        return redirect(url_for("admin.list_users"))
    return render_template("admin/user_form.html", user=u)


@bp.route("/lojas", methods=["GET", "POST"])
@admin_required
def stores():
    if request.method == "POST":
        name = request.form["name"].strip()
        if name and not Store.query.filter_by(name=name).first():
            db.session.add(Store(name=name, active=True))
            db.session.commit()
            flash("Loja adicionada.", "success")
        return redirect(url_for("admin.stores"))
    items = Store.query.order_by(Store.name).all()
    return render_template("admin/stores.html", stores=items)


@bp.route("/lojas/<int:sid>/toggle", methods=["POST"])
@admin_required
def toggle_store(sid):
    s = Store.query.get_or_404(sid)
    s.active = not s.active
    db.session.commit()
    return redirect(url_for("admin.stores"))
