from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required

from ..extensions import db
from ..models import Candidate, FunnelRecord, Store
from ..constants import INTERVIEWERS, SCREENED_BY

bp = Blueprint("funnel", __name__)


def _parse_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except Exception:
        return None


def _count_aprovados_por_data(target_date, kind, store=None, role=None, interviewer=None, screened_by=None):
    """Conta candidatos com determinado criterio de data.

    kind = 'start' -> usa Candidate.start_date == target_date
    kind = 'd1'    -> usa Candidate.interview_date == target_date
    """
    q = Candidate.query
    if kind == "start":
        q = q.filter(Candidate.start_date == target_date)
    else:
        q = q.filter(Candidate.interview_date == target_date)
    if store:
        q = q.filter(Candidate.store == store)
    if role:
        q = q.filter(Candidate.role_position == role)
    if interviewer:
        q = q.filter(Candidate.interviewer == interviewer)
    if screened_by:
        q = q.filter(Candidate.screened_by == screened_by)
    return q.count()


@bp.route("/")
@login_required
def view_funnel():
    period_start = _parse_date(request.args.get("start"))
    period_end = _parse_date(request.args.get("end"))
    store = request.args.get("store") or None
    role = request.args.get("role") or None
    interviewer = request.args.get("interviewer") or None
    screened_by = request.args.get("screened_by") or None

    q = FunnelRecord.query
    if period_start:
        q = q.filter(FunnelRecord.reference_date >= period_start)
    if period_end:
        q = q.filter(FunnelRecord.reference_date <= period_end)
    if store:
        q = q.filter(FunnelRecord.store == store)
    if role:
        q = q.filter(FunnelRecord.role_position == role)
    if interviewer:
        q = q.filter(FunnelRecord.interviewer == interviewer)
    if screened_by:
        q = q.filter(FunnelRecord.screened_by == screened_by)

    records = q.order_by(FunnelRecord.reference_date.desc()).all()

    rows = []
    for r in records:
        total_aprovados = _count_aprovados_por_data(r.reference_date, r.record_type, r.store, r.role_position, r.interviewer, r.screened_by)
        rows.append({
            "record": r,
            "total_aprovados": total_aprovados,
            "calc": _funnel_calc(total_aprovados, r),
        })

    stores = [s.name for s in Store.query.order_by(Store.name).all()]
    return render_template(
        "funnel/list.html",
        rows=rows,
        stores=stores,
        interviewers=INTERVIEWERS,
        screened_by_options=SCREENED_BY,
        filters=request.args,
    )


def _funnel_calc(total_aprovados, r: FunnelRecord):
    """Calcula perdas absolutas e percentuais entre etapas.

    Sequencia: total_aprovados -> proposta -> apresentacao -> treina -> admissao -> prorrogacao -> efetivacao
    """
    seq = [
        ("Aprovados", total_aprovados),
        ("Proposta da Vaga", r.proposta_vaga),
        ("Ap. pessoal/Cultura + form.", r.apresentacao_cultura),
        ("Treina. Func. + Premiacao", r.treina_funcional),
        ("Admissao", r.admissao),
        ("Prorrogacao", r.prorrogacao),
        ("Efetivacao", r.efetivacao),
    ]
    out = []
    prev_value = None
    for label, value in seq:
        loss = None
        pct = None
        if value is not None and prev_value is not None and prev_value > 0:
            loss = prev_value - value
            pct = round(loss / prev_value * 100, 2)
        out.append({"label": label, "value": value, "loss": loss, "pct": pct})
        if value is not None:
            prev_value = value
    return out


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def new_funnel():
    if request.method == "POST":
        r = FunnelRecord(
            record_type=request.form.get("record_type", "start"),
            reference_date=_parse_date(request.form["reference_date"]),
            store=request.form.get("store") or None,
            role_position=request.form.get("role_position") or None,
            interviewer=request.form.get("interviewer") or None,
            screened_by=request.form.get("screened_by") or None,
            proposta_vaga=_int_or_none(request.form.get("proposta_vaga")),
            apresentacao_cultura=_int_or_none(request.form.get("apresentacao_cultura")),
            treina_funcional=_int_or_none(request.form.get("treina_funcional")),
            admissao=_int_or_none(request.form.get("admissao")),
            prorrogacao=_int_or_none(request.form.get("prorrogacao")),
            efetivacao=_int_or_none(request.form.get("efetivacao")),
        )
        db.session.add(r)
        db.session.commit()
        flash("Linha de funil criada.", "success")
        return redirect(url_for("funnel.view_funnel"))

    stores = [s.name for s in Store.query.order_by(Store.name).all()]
    return render_template("funnel/form.html",
                           stores=stores,
                           interviewers=INTERVIEWERS,
                           screened_by_options=SCREENED_BY,
                           record=None)


@bp.route("/<int:rid>/editar", methods=["GET", "POST"])
@login_required
def edit_funnel(rid):
    r = FunnelRecord.query.get_or_404(rid)
    if request.method == "POST":
        r.record_type = request.form.get("record_type", r.record_type)
        r.reference_date = _parse_date(request.form["reference_date"])
        r.store = request.form.get("store") or None
        r.role_position = request.form.get("role_position") or None
        r.interviewer = request.form.get("interviewer") or None
        r.screened_by = request.form.get("screened_by") or None
        r.proposta_vaga = _int_or_none(request.form.get("proposta_vaga"))
        r.apresentacao_cultura = _int_or_none(request.form.get("apresentacao_cultura"))
        r.treina_funcional = _int_or_none(request.form.get("treina_funcional"))
        r.admissao = _int_or_none(request.form.get("admissao"))
        r.prorrogacao = _int_or_none(request.form.get("prorrogacao"))
        r.efetivacao = _int_or_none(request.form.get("efetivacao"))
        db.session.commit()
        flash("Funil atualizado.", "success")
        return redirect(url_for("funnel.view_funnel"))

    stores = [s.name for s in Store.query.order_by(Store.name).all()]
    return render_template("funnel/form.html",
                           stores=stores,
                           interviewers=INTERVIEWERS,
                           screened_by_options=SCREENED_BY,
                           record=r)


@bp.route("/aprovados")
@login_required
def api_aprovados():
    """Endpoint AJAX usado pelo formulario para mostrar 'total automatico' antes de salvar."""
    target = _parse_date(request.args.get("date"))
    kind = request.args.get("kind", "start")
    if not target:
        return jsonify({"total": 0})
    total = _count_aprovados_por_data(target, kind,
                                      request.args.get("store"),
                                      request.args.get("role"),
                                      request.args.get("interviewer"),
                                      request.args.get("screened_by"))
    return jsonify({"total": total})


def _int_or_none(v):
    try:
        if v in (None, "", "null"):
            return None
        return int(v)
    except Exception:
        return None
