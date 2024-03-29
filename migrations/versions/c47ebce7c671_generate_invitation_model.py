"""Generate invitation model

Revision ID: c47ebce7c671
Revises: f5f1fbfd6198
Create Date: 2020-01-20 16:28:31.326376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c47ebce7c671'
down_revision = 'f5f1fbfd6198'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Invitation',
    sa.Column('id', sa.String(length=21), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('role_id', sa.String(length=21), nullable=False),
    sa.Column('user_dashboard_url', sa.TEXT(), nullable=False),
    sa.Column('signup_url', sa.TEXT(), nullable=False),
    sa.Column('organisation_id', sa.String(length=21), nullable=False),
    sa.ForeignKeyConstraint(['organisation_id'], ['Organisation.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['Role.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', 'organisation_id', name='invitation_email_org_constraint')
    )
    # SeederManager.seed_database('role')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Invitation')
    # ### end Alembic commands ###
