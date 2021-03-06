"""fixed the column naming error

Revision ID: 84cbbdf1b4cd
Revises: f272d1e7d58a
Create Date: 2018-10-16 04:09:23.686120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84cbbdf1b4cd'
down_revision = 'f272d1e7d58a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('registrations', sa.Column('paid_on', sa.Date(), nullable=True))
    op.drop_column('registrations', 'paied_on')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('registrations', sa.Column('paied_on', sa.DATE(), autoincrement=False, nullable=True))
    op.drop_column('registrations', 'paid_on')
    # ### end Alembic commands ###
