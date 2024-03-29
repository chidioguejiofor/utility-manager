"""empty message

Revision ID: a57eab4c7be5
Revises: b48fecf9ffbf
Create Date: 2020-01-21 10:57:28.174469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a57eab4c7be5'
down_revision = 'b48fecf9ffbf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('membership_user_id_organisation_id_key', 'Membership', ['user_id', 'organisation_id'])
    op.drop_constraint('Membership_user_id_organisation_id_key', 'Membership', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('Membership_user_id_organisation_id_key', 'Membership', ['user_id', 'organisation_id'])
    op.drop_constraint('membership_user_id_organisation_id_key', 'Membership', type_='unique')
    # ### end Alembic commands ###
