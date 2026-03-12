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

# Enum types matching the SQLModel definitions
impact_level_enum = sa.Enum("high", "medium", name="impact_level_enum")
system_type_enum = sa.Enum(
    "bes_cyber_system", "eacms", "pacs", "pca", name="system_type_enum"
)
device_class_enum = sa.Enum(
    "windows",
    "linux",
    "network_device",
    "firewall",
    "relay",
    "rtu",
    "plc",
    "hmi",
    "historian",
    "other_ot",
    name="device_class_enum",
)
asset_status_enum = sa.Enum(
    "active", "decommissioned", "pending", name="asset_status_enum"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "assets",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("impact_level", impact_level_enum, nullable=False),
        sa.Column("system_type", system_type_enum, nullable=False),
        sa.Column("device_class", device_class_enum, nullable=False),
        sa.Column("parent_bes_cyber_system_id", sa.UUID(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        sa.Column("site", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column(
            "has_external_routable_connectivity",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "status",
            asset_status_enum,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
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
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_bes_cyber_system_id"],
            ["assets.id"],
            name="fk_assets_parent_bes_cyber_system_id",
            ondelete="SET NULL",
        ),
    )

    op.create_index("ix_assets_name", "assets", ["name"])
    op.create_index("ix_assets_impact_level", "assets", ["impact_level"])
    op.create_index("ix_assets_system_type", "assets", ["system_type"])
    op.create_index("ix_assets_device_class", "assets", ["device_class"])
    op.create_index(
        "ix_assets_parent_bes_cyber_system_id",
        "assets",
        ["parent_bes_cyber_system_id"],
    )
    op.create_index("ix_assets_site", "assets", ["site"])
    op.create_index("ix_assets_status", "assets", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("assets")
    impact_level_enum.drop(op.get_bind(), checkfirst=True)
    system_type_enum.drop(op.get_bind(), checkfirst=True)
    device_class_enum.drop(op.get_bind(), checkfirst=True)
    asset_status_enum.drop(op.get_bind(), checkfirst=True)
