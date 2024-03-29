"""empty message

Revision ID: 41efd0e44e75
Revises: 
Create Date: 2019-09-16 14:54:00.345394

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
# revision identifiers, used by Alembic.
revision = '41efd0e44e75'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'Organisation', sa.Column('id', sa.String(length=21), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('display_name', sa.String(length=120), nullable=False),
        sa.Column('website', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('subscription_type',
                  sa.Enum('FREE',
                          'BRONZE',
                          'SILVER',
                          'GOLD',
                          'DIAMOND',
                          name='subscription'),
                  nullable=False),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('email'),
        sa.UniqueConstraint('name'))
    op.create_table(
        'User', sa.Column('id', sa.String(length=21), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint('id'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('User')
    op.drop_table('Organisation')
    op.execute('DROP TYPE IF EXISTS subscription')
    # ### end Alembic commands ###
