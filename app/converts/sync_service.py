"""Servico de sincronizacao Converts -> banco local.

Fluxo:
1. Login no Converts
2. Buscar candidatos do dia
3. Buscar lista de lojas
4. Normalizar dados (mapear campos)
5. Inserir candidatos novos (evita duplicidade por nome+data+vaga)
6. Atualizar tabela 'stores'
7. Persistir SyncLog

Mapeamento de campos pedido pelo cliente (Converts -> Controle de Candidatos AP):
- Nome do candidato        -> coluna D (name)
- Vaga                     -> coluna H (role_position) -> tambem usado como Funcao
- Proxima entrevista       -> coluna A (interview_date)
- Visto por                -> coluna F (screened_by)
- Loja (de RELATORIOS)     -> coluna G (store)
"""
import logging
from datetime import date as date_cls, datetime
from typing import Optional

from flask import current_app

from ..extensions import db
from ..models import Candidate, Store, SyncLog
from .client import ConvertsClient
from .normalizer import normalize_candidate, parse_date

logger = logging.getLogger(__name__)


def _upsert_stores(stores_payload):
    inserted = 0
    for s in stores_payload or []:
        name = (s.get("nome") or s.get("name") or s.get("loja") or "").strip()
        if not name:
            continue
        cid = str(s.get("id") or s.get("loja_id") or "") or None
        existing = Store.query.filter_by(name=name).first()
        if not existing:
            db.session.add(Store(name=name, converts_id=cid, active=True))
            inserted += 1
        elif cid and not existing.converts_id:
            existing.converts_id = cid
    if inserted:
        db.session.commit()
    return inserted


def _is_duplicate(name: str, interview_date: Optional[date_cls], role_position: Optional[str]) -> bool:
    q = Candidate.query.filter(Candidate.name == name)
    if interview_date:
        q = q.filter(Candidate.interview_date == interview_date)
    if role_position:
        q = q.filter(Candidate.role_position == role_position)
    return db.session.query(q.exists()).scalar()


def run_sync(target_date: Optional[date_cls] = None, triggered_by: str = "scheduler", user_id: Optional[int] = None) -> SyncLog:
    """Executa a sincronizacao e devolve o SyncLog gravado."""
    if target_date is None:
        target_date = date_cls.today()

    log = SyncLog(triggered_by=triggered_by, user_id=user_id, started_at=datetime.utcnow(), status="running")
    db.session.add(log)
    db.session.commit()

    found = inserted = duplicates = 0
    errors = []

    try:
        client = ConvertsClient()
        client.login()

        # 1) Lojas (atualiza catalogo)
        try:
            stores = client.get_stores()
            _upsert_stores(stores)
        except Exception as exc:
            errors.append(f"stores: {exc}")
            logger.warning("Falha sincronizando lojas (continuando): %s", exc)

        # 2) Candidatos do dia
        raw_list = client.get_candidates_by_date(target_date)
        found = len(raw_list)

        for raw in raw_list:
            try:
                data = normalize_candidate(raw)
                if not data.get("name"):
                    continue
                if _is_duplicate(data["name"], data.get("interview_date"), data.get("role_position")):
                    duplicates += 1
                    continue
                cand = Candidate(
                    interview_date=data.get("interview_date"),
                    name=data["name"],
                    screened_by=data.get("screened_by"),
                    store=data.get("store"),
                    role_position=data.get("role_position"),
                    converts_id=data.get("converts_id"),
                    source="converts",
                )
                db.session.add(cand)
                inserted += 1
            except Exception as exc:
                errors.append(f"candidato {raw.get('id', '?')}: {exc}")
                logger.exception("Falha importando candidato")

        db.session.commit()
        log.status = "success"
    except Exception as exc:
        db.session.rollback()
        errors.append(str(exc))
        log.status = "failed"
        logger.exception("Sync Converts falhou")
    finally:
        log.found = found
        log.inserted = inserted
        log.duplicates = duplicates
        log.errors = ("; ".join(errors))[:4000] if errors else None
        log.finished_at = datetime.utcnow()
        db.session.commit()

    return log
