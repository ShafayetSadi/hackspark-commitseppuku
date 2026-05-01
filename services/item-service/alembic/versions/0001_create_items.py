"""create items table

Revision ID: 0001_create_items
Revises:
Create Date: 2026-04-29

"""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_items"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "items" not in inspector.get_table_names():
        op.create_table(
            "items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes("items")}
    if "ix_items_category" not in existing_indexes:
        op.create_index("ix_items_category", "items", ["category"], unique=False)
    if "ix_items_category_created_at" not in existing_indexes:
        op.create_index(
            "ix_items_category_created_at",
            "items",
            ["category", "created_at"],
            unique=False,
        )
    if "ix_items_name" not in existing_indexes:
        op.create_index("ix_items_name", "items", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_items_name", table_name="items")
    op.drop_index("ix_items_category_created_at", table_name="items")
    op.drop_index("ix_items_category", table_name="items")
    op.drop_table("items")
