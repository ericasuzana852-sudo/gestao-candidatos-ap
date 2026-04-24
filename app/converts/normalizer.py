"""Normalizacao do payload do Converts -> dict pronto para o modelo Candidate.

FAcil de ajustar conforme o JSON real retornado pelo Converts.
"""
from datetime import datetime, date
from typing import Optional, Dict, Any


def parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
               "%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y"]
    for f in formats:
        try:
            return datetime.strptime(s[:len(f) + 4], f).date()
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


def _pick(d: Dict[str, Any], *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def normalize_candidate(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Mapeia o payload do Converts para os campos do nosso Candidate.

    AJUSTE conforme o JSON real. As keys abaixo cobrem variacoes
    comuns (PT-BR e EN).
    """
    name = _pick(raw, "nome", "nome_candidato", "candidato", "name", "candidate_name")
    interview = _pick(raw, "proxima_entrevista", "data_entrevista", "interview_date", "data")
    role_position = _pick(raw, "vaga", "funcao", "role", "position")
    screened_by = _pick(raw, "visto_por", "triagem_por", "screened_by", "recrutador")
    store = _pick(raw, "loja", "unidade", "store", "loja_nome")
    cid = _pick(raw, "id", "_id", "candidato_id")

    return {
        "name": (name or "").strip(),
        "interview_date": parse_date(interview),
        "role_position": (role_position or None),
        "screened_by": (screened_by or None),
        "store": (store or None),
        "converts_id": str(cid) if cid is not None else None,
    }
