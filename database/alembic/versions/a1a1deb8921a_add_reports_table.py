"""add reports table

Revision ID: a1a1deb8921a
Revises: 7f1dab0c1aa3
Create Date: 2026-06-26 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1a1deb8921a'
down_revision: Union[str, None] = '7f1dab0c1aa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if the Enum types are registered in PostgreSQL or SQLite
    op.create_table('reports',
    sa.Column('report_type', sa.String(length=32), nullable=False),
    sa.Column('format', sa.String(length=10), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('pending', 'completed', 'failed', name='report_status'), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('content', sa.LargeBinary(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('generated_by', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_severity'), 'alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_alerts_status'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_severity'), table_name='alerts')
    op.drop_table('reports')
    # Try to drop the enum type if in postgres
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE report_status')
