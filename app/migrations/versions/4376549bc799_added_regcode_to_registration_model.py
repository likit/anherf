"""added regcode to registration model

Revision ID: 4376549bc799
Revises: 84cbbdf1b4cd
Create Date: 2018-10-29 04:30:01.127889

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4376549bc799'
down_revision = '84cbbdf1b4cd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('registrations', sa.Column('regcode', sa.String(length=16), nullable=True))
    op.create_unique_constraint(None, 'registrations', ['regcode'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'registrations', type_='unique')
    op.drop_column('registrations', 'regcode')
    # ### end Alembic commands ###
