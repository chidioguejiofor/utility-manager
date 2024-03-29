"""Create Membership and Organisation models

Revision ID: 4889bb8c5a74
Revises: 41efd0e44e75
Create Date: 2019-09-19 10:59:20.843984

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4889bb8c5a74'
down_revision = '41efd0e44e75'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Membership',
    sa.Column('id', sa.String(length=21), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('user_id', sa.String(length=21), nullable=True),
    sa.Column('organisation_id', sa.String(length=21), nullable=True),
    sa.Column('role', sa.Enum('OWNER', 'ENGINEER', 'MANAGER', 'REGULAR_USER', name='role'), nullable=False),
    sa.ForeignKeyConstraint(['organisation_id'], ['Organisation.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['User.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'organisation_id')
    )
    op.add_column('User', sa.Column('email', sa.String(length=320), nullable=False))
    op.add_column('User', sa.Column('first_name', sa.String(length=20), nullable=False))
    op.add_column('User', sa.Column('last_name', sa.String(length=20), nullable=False))
    op.add_column('User', sa.Column('password_hash', sa.VARCHAR(length=130), nullable=False))
    op.add_column('User', sa.Column('verified', sa.BOOLEAN(), nullable=False))
    op.create_unique_constraint('user_email_unique_constraint', 'User', ['email'])
    op.drop_column('User', 'name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('User', sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.drop_constraint('user_email_unique_constraint', 'User', type_='unique')
    op.drop_column('User', 'verified')
    op.drop_column('User', 'password_hash')
    op.drop_column('User', 'last_name')
    op.drop_column('User', 'first_name')
    op.drop_column('User', 'email')
    op.drop_table('Membership')
    op.execute('DROP TYPE role')
    # ### end Alembic commands ###
