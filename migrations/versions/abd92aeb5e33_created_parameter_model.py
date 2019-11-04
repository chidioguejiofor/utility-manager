"""Created Parameter Model

Revision ID: abd92aeb5e33
Revises: c564f76264f5
Create Date: 2019-10-31 13:43:36.135734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abd92aeb5e33'
down_revision = 'c564f76264f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Parameter',
    sa.Column('id', sa.String(length=21), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('unit_id', sa.String(), nullable=True),
    sa.Column('validation', sa.String(), nullable=True),
    sa.Column('required', sa.BOOLEAN(), nullable=False),
    sa.Column('value_type', sa.Enum('NUMERIC', 'STRING', 'DATE_TIME', 'DATE', 'ENUM', name='value_type_enum'), nullable=False),
    sa.Column('organisation_id', sa.String(length=21), nullable=True),
    sa.Column('created_by_id', sa.String(length=21), nullable=True),
    sa.Column('updated_by_id', sa.String(length=21), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['User.id'], onupdate='CASCADE', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['organisation_id'], ['Organisation.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['unit_id'], ['Unit.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['User.id'], onupdate='CASCADE', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'organisation_id', name='parameter_name_and_org_unique_constraint')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Parameter')
    # ### end Alembic commands ###
    op.execute('DROP TYPE IF EXISTS   value_type_enum')