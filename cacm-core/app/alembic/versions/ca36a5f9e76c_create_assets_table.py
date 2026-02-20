"""create assets table

Revision ID: ca36a5f9e76c
Revises:
Create Date: 2026-02-19 22:46:25.163707

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ca36a5f9e76c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "assets",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        # Created At and Updated At with timezone-aware timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        # Parent BES Cyber System association
        sa.Column("parent_bes_cyber_system_id", sa.UUID(), nullable=True),
    )

    op.create_index(
        "ix_assets_parent_bes_cyber_system_id",
        "assets",
        ["parent_bes_cyber_system_id"],
    )

    op.create_foreign_key(
        "fk_assets_parent_bes_cyber_system_id",
        source_table="assets",
        referent_table="bes_cyber_systems",
        local_columns=["parent_bes_cyber_system_id"],
        remote_columns=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_assets_parent_bes_cyber_system_id", "assets", type_="foreignkey"
    )
    op.drop_index("ix_assets_parent_bes_cyber_system_id", table_name="assets")
    op.drop_table("assets")
