from datetime import datetime
from collections import defaultdict

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Candidate, Store
from ..constants import LOSS_STAGES, ADMISSION_STAGES, INTERVIEWERS

bp = Blueprint("reports", __name__)


def _parse_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except Exception:
        return None


@bp.route("/")
@login_required
def view_reports():
    period_start = _parse_date(request.args.get("start"))
    period_end = _parse_date(request.args.get("end"))
    store = request.args.get("store") or None
    role = request.args.get("role") or None
    interviewer = request.args.get("interviewer") or None

    q = Candidate.query
    if period_start:
        q = q.filter(Candidate.interview_date >= period_start)
    if period_end:
        q = q.filter(Candidate.interview_date <= period_end)
    if store:
        q = q.filter(Candidate.store == store)
    if role:
        q = q.filter(Candidate.role_position == role)
    if interviewer:
        q = q.filter(Candidate.interviewer == interviewer)

    candidates = q.all()

    total = len(candidates)
    desistencias = sum(1 for c in candidates if c.stage in {"Desistiu", "Desistiu Treina."})
    cortes = sum(1 for c in candidates if c.stage == "Corte/Processo")
    admissoes = sum(1 for c in candidates if c.stage in ADMISSION_STAGES or c.admission_date)
    prorrogacoes = sum(1 for c in candidates if (c.extension or "").lower() == "sim")
    efetivacoes = sum(1 for c in candidates if (c.effective or "").lower() == "sim")
    perdas = sum(1 for c in candidates if c.stage in LOSS_STAGES)
    pct_perda = round(perdas / total * 100, 2) if total else 0

    perdas_etapa = defaultdict(int)
    perdas_loja = defaultdict(int)
    perdas_funcao = defaultdict(int)
    for c in candidates:
        if c.stage in LOSS_STAGES:
            perdas_etapa[c.stage] += 1
            if c.store:
                perdas_loja[c.store] += 1
            if c.role_position:
                perdas_funcao[c.role_position] += 1

    stores = [s.name for s in Store.query.order_by(Store.name).all()]
    return render_template(
        "reports/index.html",
        total=total,
        desistencias=desistencias,
        cortes=cortes,
        admissoes=admissoes,
        prorrogacoes=prorrogacoes,
        efetivacoes=efetivacoes,
        perdas=perdas,
        pct_perda=pct_perda,
        perdas_etapa=dict(perdas_etapa),
        perdas_loja=dict(perdas_loja),
        perdas_funcao=dict(perdas_funcao),
        stores=stores,
        interviewers=INTERVIEWERS,
        filters=request.args,
    )
