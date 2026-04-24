"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(120), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='operacional'),
        sa.Column('active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime),
    )

    op.create_table(
        'stores',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(180), nullable=False, unique=True),
        sa.Column('converts_id', sa.String(80)),
        sa.Column('active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime),
    )

    op.create_table(
        'candidates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('interview_date', sa.Date),
        sa.Column('start_date', sa.Date),
        sa.Column('admission_date', sa.Date),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('interviewer', sa.String(80)),
        sa.Column('screened_by', sa.String(80)),
        sa.Column('store', sa.String(180)),
        sa.Column('role_position', sa.String(120)),
        sa.Column('stage', sa.String(60)),
        sa.Column('extension', sa.String(10)),
        sa.Column('effective', sa.String(10)),
        sa.Column('reference', sa.String(10)),
        sa.Column('archived_sults', sa.String(10)),
        sa.Column('notes', sa.Text),
        sa.Column('positive_points', sa.Text),
        sa.Column('negative_points', sa.Text),
        sa.Column('score_negotiation', sa.Integer),
        sa.Column('score_history', sa.Integer),
        sa.Column('score_emotional', sa.Integer),
        sa.Column('score_posture', sa.Integer),
        sa.Column('score_alignment', sa.Integer),
        sa.Column('score_analytical', sa.Integer),
        sa.Column('score_friendly', sa.Integer),
        sa.Column('score_trainability', sa.Integer),
        sa.Column('score_political', sa.Integer),
        sa.Column('converts_id', sa.String(80)),
        sa.Column('source', sa.String(20), server_default='manual'),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('name', 'interview_date', 'role_position', name='uq_candidate_dedup'),
    )
    op.create_index('ix_candidate_search', 'candidates', ['name', 'interview_date'])

    op.create_table(
        'funnel_records',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('record_type', sa.String(20), nullable=False),
        sa.Column('reference_date', sa.Date, nullable=False),
        sa.Column('store', sa.String(180)),
        sa.Column('role_position', sa.String(120)),
        sa.Column('interviewer', sa.String(80)),
        sa.Column('screened_by', sa.String(80)),
        sa.Column('proposta_vaga', sa.Integer),
        sa.Column('apresentacao_cultura', sa.Integer),
        sa.Column('treina_funcional', sa.Integer),
        sa.Column('admissao', sa.Integer),
        sa.Column('prorrogacao', sa.Integer),
        sa.Column('efetivacao', sa.Integer),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('finished_at', sa.DateTime),
        sa.Column('triggered_by', sa.String(20), server_default='scheduler'),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('found', sa.Integer, server_default='0'),
        sa.Column('inserted', sa.Integer, server_default='0'),
        sa.Column('duplicates', sa.Integer, server_default='0'),
        sa.Column('errors', sa.Text),
        sa.Column('status', sa.String(20), server_default='running'),
    )

    op.create_table(
        'list_options',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('list_name', sa.String(60), nullable=False),
        sa.Column('value', sa.String(120), nullable=False),
        sa.Column('active', sa.Boolean, server_default=sa.text('true')),
        sa.UniqueConstraint('list_name', 'value', name='uq_list_option'),
    )


def downgrade():
    op.drop_table('list_options')
    op.drop_table('sync_logs')
    op.drop_table('funnel_records')
    op.drop_index('ix_candidate_search', table_name='candidates')
    op.drop_table('candidates')
    op.drop_table('stores')
    op.drop_table('users')
