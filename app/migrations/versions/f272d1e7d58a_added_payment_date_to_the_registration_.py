"""added payment date to the registration model

Revision ID: f272d1e7d58a
Revises: c96450ab3cfb
Create Date: 2018-10-16 04:07:55.637495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f272d1e7d58a'
down_revision = 'c96450ab3cfb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('registrations', sa.Column('paied_on', sa.Date(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('registrations', 'paied_on')
    # ### end Alembic commands ###
