"""fix_workspace_type_enum_values

Revision ID: 2601d5d2aaaa
Revises: e7f8g9h0i1j2
Create Date: 2026-01-19 15:44:17.482962

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2601d5d2aaaa'
down_revision: str | Sequence[str] | None = 'e7f8g9h0i1j2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Fix enum values from UPPERCASE (PERSONAL, TEAM) to lowercase (personal, team)
    to match the Python Enum .value definitions.
    """
    # 1. First, alter column to use varchar temporarily (must do this before updating data)
    op.execute("ALTER TABLE workspaces ALTER COLUMN workspace_type TYPE VARCHAR(20)")

    # 2. Update existing data from uppercase to lowercase
    op.execute("UPDATE workspaces SET workspace_type = 'personal' WHERE workspace_type = 'PERSONAL'")
    op.execute("UPDATE workspaces SET workspace_type = 'team' WHERE workspace_type = 'TEAM'")

    # 3. Drop old enum type
    op.execute("DROP TYPE IF EXISTS workspacetype")

    # 4. Create new enum type with lowercase values
    op.execute("CREATE TYPE workspacetype AS ENUM ('personal', 'team')")

    # 5. Convert column back to enum type
    op.execute("ALTER TABLE workspaces ALTER COLUMN workspace_type TYPE workspacetype USING workspace_type::workspacetype")


def downgrade() -> None:
    """Downgrade schema.

    Revert enum values from lowercase to UPPERCASE.
    """
    # 1. Convert column to varchar temporarily
    op.execute("ALTER TABLE workspaces ALTER COLUMN workspace_type TYPE VARCHAR(20)")

    # 2. Update data from lowercase to uppercase
    op.execute("UPDATE workspaces SET workspace_type = 'PERSONAL' WHERE workspace_type = 'personal'")
    op.execute("UPDATE workspaces SET workspace_type = 'TEAM' WHERE workspace_type = 'team'")

    # 3. Recreate enum with uppercase values
    op.execute("DROP TYPE IF EXISTS workspacetype")
    op.execute("CREATE TYPE workspacetype AS ENUM ('PERSONAL', 'TEAM')")

    # 4. Convert column back to enum type
    op.execute("ALTER TABLE workspaces ALTER COLUMN workspace_type TYPE workspacetype USING workspace_type::workspacetype")
