"""Update Unit model

Revision ID: c78e26fafbff
Revises: 8ae48170fa1d
Create Date: 2020-04-19 15:28:31.875628

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c78e26fafbff'
down_revision = '8ae48170fa1d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('unit_name_and_greek_symbol_when_org_is_null', table_name='Unit')
    op.drop_constraint('unit_name_and_greeksymbolnum_unique_constraint', 'Unit', type_='unique')
    op.drop_constraint('unit_name_and_letter_symbol_unique_constraint', 'Unit', type_='unique')
    op.drop_index('unit_name_and_letter_when_org_is_null', table_name='Unit')
    op.drop_column('Unit', 'greek_symbol_num')
    # op.drop_column('Unit', 'letter_symbol')
    op.alter_column('Unit', 'letter_symbol', new_column_name='symbol')
    op.execute(
        """
        UPDATE "Unit"
        SET symbol='\u2126'    
        WHERE name='Ohms'
        """
    )
    op.alter_column('Unit', 'symbol', nullable=False)
    op.create_unique_constraint('unit_name_and_symbol_unique_constraint', 'Unit', ['name', 'symbol', 'organisation_id'])
    op.create_index('unit_name_and_letter_when_org_is_null', 'Unit', ['name', 'symbol'], unique=True,
                    postgresql_where=sa.text('organisation_id IS NULL'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP INDEX IF EXISTS "unit_name_and_letter_when_org_is_null" ')
    op.drop_constraint('unit_name_and_symbol_unique_constraint', 'Unit', type_='unique')
    op.alter_column('Unit', 'symbol', new_column_name='letter_symbol', nullable=True)
    op.alter_column('Unit', 'letter_symbol',  sa.VARCHAR(length=5))
    op.add_column('Unit', sa.Column('greek_symbol_num', sa.SMALLINT(), autoincrement=False, nullable=True))
    op.create_index('unit_name_and_letter_when_org_is_null', 'Unit', ['name', 'letter_symbol'], unique=True)
    op.create_unique_constraint('unit_name_and_letter_symbol_unique_constraint', 'Unit', ['name', 'letter_symbol', 'organisation_id'])
    op.create_unique_constraint('unit_name_and_greeksymbolnum_unique_constraint', 'Unit', ['name', 'greek_symbol_num', 'organisation_id'])
    op.create_index('unit_name_and_greek_symbol_when_org_is_null', 'Unit', ['name', 'greek_symbol_num'], unique=True)
    op.execute(
        """
        UPDATE "Unit"
        SET letter_symbol=NULL,  greek_symbol_num=48   
        WHERE name='Ohms'
        """
    )
    # ### end Alembic commands ###
