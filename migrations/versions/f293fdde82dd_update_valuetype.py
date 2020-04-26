"""Update ValueType

Revision ID: f293fdde82dd
Revises: 13a5ae8f1e7b
Create Date: 2020-04-26 01:05:26.915904

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f293fdde82dd'
down_revision = '13a5ae8f1e7b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TYPE value_type_enum RENAME VALUE 'STRING' TO 'TEXT';
    """)


def downgrade():
    op.execute("""
        ALTER TYPE value_type_enum RENAME VALUE  'TEXT' TO 'STRING';
        """)
