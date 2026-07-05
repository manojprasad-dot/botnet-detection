"""add heartbeat and response action tables

Revision ID: 2984920c812d
Revises: 8cdf24fcb8b8
Create Date: 2026-07-05 18:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2984920c812d'
down_revision: Union[str, None] = '8cdf24fcb8b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Heartbeats Table ──────────────────────────────────────────────────
    op.create_table('heartbeats',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('device_id', sa.String(), nullable=False),
    sa.Column('cpu_percent', sa.Float(), nullable=True),
    sa.Column('ram_percent', sa.Float(), nullable=True),
    sa.Column('disk_percent', sa.Float(), nullable=True),
    sa.Column('uptime_seconds', sa.Integer(), nullable=True),
    sa.Column('agent_version', sa.String(), nullable=True),
    sa.Column('capture_status', sa.String(), nullable=True),
    sa.Column('flows_processed', sa.Integer(), nullable=True),
    sa.Column('packets_captured', sa.Integer(), nullable=True),
    sa.Column('threats_detected', sa.Integer(), nullable=True),
    sa.Column('queue_depth', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_heartbeats_device_id'), 'heartbeats', ['device_id'], unique=False)

    # ── Response Actions Table ─────────────────────────────────────────────
    op.create_table('response_actions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('device_id', sa.String(), nullable=False),
    sa.Column('action_type', sa.String(), nullable=False),
    sa.Column('target', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('triggered_by', sa.String(), nullable=True),
    sa.Column('risk_score', sa.Integer(), nullable=True),
    sa.Column('alert_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_response_actions_device_id'), 'response_actions', ['device_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_response_actions_device_id'), table_name='response_actions')
    op.drop_table('response_actions')
    op.drop_index(op.f('ix_heartbeats_device_id'), table_name='heartbeats')
    op.drop_table('heartbeats')
