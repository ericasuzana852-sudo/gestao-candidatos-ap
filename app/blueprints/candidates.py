from datetime import datetime, date
from io import BytesIO

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, abort, send_file, jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy import or_
from openpyxl import Workbook

from ..extensions import db
from ..models import Candidate, Store
from ..constants import (
    INTERVIEWERS, SCREENED_BY, STAGES, YES_NO,
    POSITIVE_POINTS, NEGATIVE_POINTS,
)

bp = Blueprint("candidates", __name__)


def _parse_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_int_score(v):
    if v in (None, "", "Sem nota"):
        return None
    try:
        n = int(v)
        return n if 1 <= n <= 5 else None
    except Exception:
        return None


def _list_filters(query):
    period_start = _parse_date(request.args.get("start"))
    period_end = _parse_date(request.args.get("end"))
    store = request.args.get("store") or None
    role = request.args.get("role") or None
    stage = request.args.get("stage") or None
    interviewer = request.args.get("interviewer") or None
    screened_by = request.args.get("screened_by") or None
    search = (request.args.get("q") or "").strip()

    if period_start:
        query = query.filter(Candidate.interview_date >= period_start)
    if period_end:
        query = query.filter(Candidate.interview_date <= period_end)
    if store:
        query = query.filter(Candidate.store == store)
    if role:
        query = query.filter(Candidate.role_position == role)
    if stage:
        query = query.filter(Candidate.stage == stage)
    if interviewer:
        query = query.filter(Candidate.interviewer == interviewer)
    if screened_by:
        query = query.filter(Candidate.screened_by == screened_by)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Candidate.name.ilike(like), Candidate.role_position.ilike(like)))

    return query


def _render_form_context(candidate=None):
    stores = [s.name for s in Store.query.order_by(Store.name).all()]
    return dict(
        candidate=candidate,
        interviewers=INTERVIEWERS,
        screened_by_options=SCREENED_BY,
        stages=STAGES,
        yes_no=YES_NO,
        positive_points=POSITIVE_POINTS,
        negative_points=NEGATIVE_POINTS,
        stores=stores,
        score_options=["Sem nota", 1, 2, 3, 4, 5],
    )


@bp.route("/")
@login_required
def list_candidates():
    q = Candidate.query
    q = _list_filters(q)
    candidates = q.order_by(Candidate.interview_date.desc().nullslast(), Candidate.id.desc()).limit(500).all()
    stores = [s.name for s in Store.query.order_by(Store.name).all()]
    roles = sorted({c.role_position for c in Candidate.query.with_entities(Candidate.role_position).distinct() if c.role_position})
    return render_template(
        "candidates/list.html",
        candidates=candidates,
        stores=stores,
        roles=roles,
        stages=STAGES,
        interviewers=INTERVIEWERS,
        screened_by_options=SCREENED_BY,
        filters=request.args,
    )


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def new_candidate():
    if request.method == "POST":
        c = Candidate(name=request.form["name"].strip(), source="manual")
        _apply_form(c)
        db.session.add(c)
        db.session.commit()
        flash("Candidato cadastrado.", "success")
        return redirect(url_for("candidates.list_candidates"))
    return render_template("candidates/form.html", **_render_form_context())


@bp.route("/<int:cid>/editar", methods=["GET", "POST"])
@login_required
def edit_candidate(cid):
    c = Candidate.query.get_or_404(cid)
    if request.method == "POST":
        _apply_form(c)
        db.session.commit()
        flash("Candidato atualizado.", "success")
        return redirect(url_for("candidates.list_candidates"))
    return render_template("candidates/form.html", **_render_form_context(c))


@bp.route("/<int:cid>/excluir", methods=["POST"])
@login_required
def delete_candidate(cid):
    if not current_user.is_admin:
        abort(403)
    c = Candidate.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash("Candidato excluido.", "success")
    return redirect(url_for("candidates.list_candidates"))


def _apply_form(c: Candidate):
    c.name = request.form["name"].strip()
    c.interview_date = _parse_date(request.form.get("interview_date"))
    c.start_date = _parse_date(request.form.get("start_date"))
    c.admission_date = _parse_date(request.form.get("admission_date"))
    c.interviewer = request.form.get("interviewer") or None
    c.screened_by = request.form.get("screened_by") or None
    c.store = request.form.get("store") or None
    c.role_position = request.form.get("role_position") or None
    c.stage = request.form.get("stage") or None
    c.extension = request.form.get("extension") or None
    c.effective = request.form.get("effective") or None
    c.reference = request.form.get("reference") or None
    c.archived_sults = request.form.get("archived_sults") or None
    c.notes = request.form.get("notes") or None
    c.positive_points = ";".join(request.form.getlist("positive_points"))
    c.negative_points = ";".join(request.form.getlist("negative_points"))
    c.score_negotiation = _parse_int_score(request.form.get("score_negotiation"))
    c.score_history = _parse_int_score(request.form.get("score_history"))
    c.score_emotional = _parse_int_score(request.form.get("score_emotional"))
    c.score_posture = _parse_int_score(request.form.get("score_posture"))
    c.score_alignment = _parse_int_score(request.form.get("score_alignment"))
    c.score_analytical = _parse_int_score(request.form.get("score_analytical"))
    c.score_friendly = _parse_int_score(request.form.get("score_friendly"))
    c.score_trainability = _parse_int_score(request.form.get("score_trainability"))
    c.score_political = _parse_int_score(request.form.get("score_political"))


@bp.route("/exportar")
@login_required
def export_excel():
    q = _list_filters(Candidate.query).order_by(Candidate.interview_date.desc().nullslast())
    items = q.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Candidatos AP"
    headers = [
        "A Data Entrevista", "B Data Inicio Loja", "C Data Admissao",
        "D Nome", "E Entrevistador", "F Triagem", "G Loja", "H Funcao",
        "I Etapa", "J Prorrogacao", "K Efetivacao", "L Referencia",
        "M Arquivado Sults", "N Observacoes", "O Pontos +", "P Pontos -",
        "Q Negociacao", "R Historico", "S Emocional", "T Postura",
        "U Alinhamento", "V Analitica", "W Simpatia", "X Treinabilidade",
        "Y Politico", "Z Media",
    ]
    ws.append(headers)
    for c in items:
        ws.append([
            c.interview_date, c.start_date, c.admission_date, c.name,
            c.interviewer, c.screened_by, c.store, c.role_position,
            c.stage, c.extension, c.effective, c.reference,
            c.archived_sults, c.notes,
            "; ".join(c.positive_points_list), "; ".join(c.negative_points_list),
            c.score_negotiation, c.score_history, c.score_emotional, c.score_posture,
            c.score_alignment, c.score_analytical, c.score_friendly,
            c.score_trainability, c.score_political, c.average_score,
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f"candidatos_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=fname,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
