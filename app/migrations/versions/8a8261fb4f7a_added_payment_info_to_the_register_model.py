"""added payment info to the register model

Revision ID: 8a8261fb4f7a
Revises: 4d1052806fec
Create Date: 2018-10-06 03:47:25.030542

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a8261fb4f7a'
down_revision = '4d1052806fec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('registrations', sa.Column('pay_status', sa.Boolean(), nullable=True))
    op.add_column('registrations', sa.Column('payment_required', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('registrations', 'payment_required')
    op.drop_column('registrations', 'pay_status')
    # ### end Alembic commands ###
