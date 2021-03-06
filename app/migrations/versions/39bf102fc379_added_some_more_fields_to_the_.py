"""added some more fields to the participant model

Revision ID: 39bf102fc379
Revises: 8c55a1285df2
Create Date: 2019-11-18 08:54:44.301764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39bf102fc379'
down_revision = '8c55a1285df2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('participants', sa.Column('department', sa.String(), nullable=True))
    op.add_column('participants', sa.Column('fax', sa.String(), nullable=True))
    op.add_column('participants', sa.Column('officephone', sa.String(), nullable=True))
    op.add_column('participants', sa.Column('profession', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('participants', 'profession')
    op.drop_column('participants', 'officephone')
    op.drop_column('participants', 'fax')
    op.drop_column('participants', 'department')
    # ### end Alembic commands ###
