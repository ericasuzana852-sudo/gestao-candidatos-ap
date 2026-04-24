"""Modelos do banco de dados.

Tabelas:
- users
- stores
- candidates
- funnel_records
- sync_logs
- list_options
"""
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, Index

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="operacional")  # admin | operacional
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def is_admin(self):
        return self.role == "admin"


class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), unique=True, nullable=False, index=True)
    converts_id = db.Column(db.String(80), nullable=True, index=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)

    # A - Data de Entrevista (puxada do Converts)
    interview_date = db.Column(db.Date, nullable=True, index=True)
    # B - Data Inicio Loja (manual)
    start_date = db.Column(db.Date, nullable=True)
    # C - Data da Admissao (manual)
    admission_date = db.Column(db.Date, nullable=True)
    # D - Nome do Candidato (Converts)
    name = db.Column(db.String(200), nullable=False, index=True)
    # E - Entrevistador (manual)
    interviewer = db.Column(db.String(80), nullable=True)
    # F - Triagem feita por (Converts/manual)
    screened_by = db.Column(db.String(80), nullable=True)
    # G - Loja (Converts em Relatorios)
    store = db.Column(db.String(180), nullable=True, index=True)
    # H - Funcao (Converts pela vaga)
    role_position = db.Column(db.String(120), nullable=True, index=True)
    # I - Etapa
    stage = db.Column(db.String(60), nullable=True, index=True)
    # J - Prorrogacao
    extension = db.Column(db.String(10), nullable=True)  # Sim / Nao
    # K - Efetivacao
    effective = db.Column(db.String(10), nullable=True)
    # L - Referencia
    reference = db.Column(db.String(10), nullable=True)
    # M - Arquivado Sults
    archived_sults = db.Column(db.String(10), nullable=True)
    # N - Observacoes Gerais
    notes = db.Column(db.Text, nullable=True)
    # O - Pontos positivos (CSV)
    positive_points = db.Column(db.Text, nullable=True)
    # P - Pontos negativos (CSV)
    negative_points = db.Column(db.Text, nullable=True)

    # Q-Y - Notas (1 a 5 ou null = sem nota)
    score_negotiation = db.Column(db.Integer, nullable=True)
    score_history = db.Column(db.Integer, nullable=True)
    score_emotional = db.Column(db.Integer, nullable=True)
    score_posture = db.Column(db.Integer, nullable=True)
    score_alignment = db.Column(db.Integer, nullable=True)
    score_analytical = db.Column(db.Integer, nullable=True)
    score_friendly = db.Column(db.Integer, nullable=True)
    score_trainability = db.Column(db.Integer, nullable=True)
    score_political = db.Column(db.Integer, nullable=True)

    # Sincronizacao
    converts_id = db.Column(db.String(80), nullable=True, index=True)
    source = db.Column(db.String(20), default="manual")  # manual | converts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("name", "interview_date", "role_position", name="uq_candidate_dedup"),
        Index("ix_candidate_search", "name", "interview_date"),
    )

    @property
    def average_score(self):
        """Z - Media. Considera apenas notas numericas."""
        scores = [
            self.score_negotiation, self.score_history, self.score_emotional,
            self.score_posture, self.score_alignment, self.score_analytical,
            self.score_friendly, self.score_trainability, self.score_political,
        ]
        nums = [s for s in scores if s is not None]
        if not nums:
            return None
        return round(sum(nums) / len(nums), 2)

    @property
    def positive_points_list(self):
        return [p for p in (self.positive_points or "").split(";") if p]

    @property
    def negative_points_list(self):
        return [p for p in (self.negative_points or "").split(";") if p]


class FunnelRecord(db.Model):
    """Funil de contratacao - duas linhas: Data de Inicio e Data de D+1."""
    __tablename__ = "funnel_records"

    id = db.Column(db.Integer, primary_key=True)
    record_type = db.Column(db.String(20), nullable=False, index=True)  # 'start' | 'd1'
    reference_date = db.Column(db.Date, nullable=False, index=True)

    # Filtros opcionais
    store = db.Column(db.String(180), nullable=True, index=True)
    role_position = db.Column(db.String(120), nullable=True)
    interviewer = db.Column(db.String(80), nullable=True)
    screened_by = db.Column(db.String(80), nullable=True)

    # Valores manuais das etapas
    proposta_vaga = db.Column(db.Integer, nullable=True)
    apresentacao_cultura = db.Column(db.Integer, nullable=True)
    treina_funcional = db.Column(db.Integer, nullable=True)
    admissao = db.Column(db.Integer, nullable=True)
    prorrogacao = db.Column(db.Integer, nullable=True)
    efetivacao = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncLog(db.Model):
    __tablename__ = "sync_logs"

    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    triggered_by = db.Column(db.String(20), default="scheduler")  # scheduler | manual
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    found = db.Column(db.Integer, default=0)
    inserted = db.Column(db.Integer, default=0)
    duplicates = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="running")  # running | success | failed

    user = db.relationship("User")


class ListOption(db.Model):
    """Listas configuraveis (entrevistadores, etapas, etc) - opcional."""
    __tablename__ = "list_options"

    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(60), nullable=False, index=True)
    value = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("list_name", "value", name="uq_list_option"),
    )
