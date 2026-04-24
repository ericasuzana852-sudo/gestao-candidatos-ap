"""Cliente HTTP do Converts.

IMPORTANTE - ENDPOINTS A CONFIRMAR
----------------------------------
A estrutura abaixo esta pronta para uso, mas os endpoints REAIS
precisam ser confirmados (token, paths, payloads). Ajuste em:

  - login()                -> POST de autenticacao
  - get_candidates_by_date -> GET 'GESTAO DE CANDIDATOS' filtrado por data
  - get_stores             -> GET lista de lojas em RELATORIOS

Nenhuma credencial fica no codigo: tudo vem de variaveis de ambiente.
"""
import logging
from datetime import date as date_cls
from typing import List, Dict, Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)


class ConvertsClient:
    def __init__(self, base_url: Optional[str] = None,
                 login: Optional[str] = None,
                 password: Optional[str] = None,
                 timeout: int = 30):
        cfg = current_app.config
        self.base_url = (base_url or cfg.get("CONVERTS_BASE_URL", "")).rstrip("/")
        self.login_user = login or cfg.get("CONVERTS_LOGIN", "")
        self.password = password or cfg.get("CONVERTS_SENHA", "")
        self.timeout = timeout
        self.session = requests.Session()
        self._token: Optional[str] = None

    # ------------------------------------------------------------------
    # AUTENTICACAO
    # ------------------------------------------------------------------
    def login(self) -> str:
        """Autentica no Converts.

        TODO: confirmar endpoint e payload exatos.
        Padrao mais comum: POST /api/auth/login com {email, password}.
        """
        if not self.base_url or not self.login_user or not self.password:
            raise RuntimeError(
                "Credenciais Converts ausentes. Configure CONVERTS_BASE_URL, "
                "CONVERTS_LOGIN e CONVERTS_SENHA no .env / Render."
            )

        url = f"{self.base_url}/api/auth/login"  # AJUSTE SE NECESSARIO
        payload = {"email": self.login_user, "password": self.password}
        try:
            r = self.session.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json() if r.content else {}
            # AJUSTE: o nome do campo do token pode ser 'token', 'access_token', 'jwt'
            self._token = data.get("token") or data.get("access_token") or data.get("jwt")
            if self._token:
                self.session.headers.update({"Authorization": f"Bearer {self._token}"})
            return self._token or ""
        except requests.HTTPError as exc:
            logger.error("Falha login Converts: %s - %s", exc, getattr(exc.response, 'text', ''))
            raise

    def _ensure_login(self):
        if not self._token:
            self.login()

    # ------------------------------------------------------------------
    # CANDIDATOS
    # ------------------------------------------------------------------
    def get_candidates_by_date(self, target_date: date_cls) -> List[Dict]:
        """Retorna candidatos da data informada.

        Caminho no Converts: GESTAO DE CANDIDATOS > filtrar pela data atual.
        TODO: confirmar endpoint e nome dos parametros de filtro.
        """
        self._ensure_login()
        url = f"{self.base_url}/api/candidatos"  # AJUSTE
        params = {
            "data_inicio": target_date.isoformat(),
            "data_fim": target_date.isoformat(),
        }
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            # AJUSTE: o payload pode vir como list, ou {"data": [...]}, ou {"items": [...]}.
            if isinstance(data, dict):
                return data.get("data") or data.get("items") or data.get("candidatos") or []
            return data or []
        except requests.HTTPError as exc:
            logger.error("Falha buscando candidatos: %s", exc)
            raise

    # ------------------------------------------------------------------
    # LOJAS
    # ------------------------------------------------------------------
    def get_stores(self) -> List[Dict]:
        """Retorna a lista de lojas (RELATORIOS).

        TODO: confirmar endpoint exato. Pode ser /api/relatorios/lojas
        ou /api/lojas.
        """
        self._ensure_login()
        url = f"{self.base_url}/api/relatorios/lojas"  # AJUSTE
        try:
            r = self.session.get(url, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict):
                return data.get("data") or data.get("items") or data.get("lojas") or []
            return data or []
        except requests.HTTPError as exc:
            logger.error("Falha buscando lojas: %s", exc)
            raise
