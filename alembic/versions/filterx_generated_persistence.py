"""FilterX generated persistence blueprint.

This file is intentionally conservative and non-destructive.
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = 'filterx_generated_persistence'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add concrete operations after reviewing generated feature gates.
    # saved_filters=True
    # shared_filters=False
    # auditing=False
    pass


def downgrade() -> None:
    # Reverse of upgrade() must remain non-destructive by default.
    pass
