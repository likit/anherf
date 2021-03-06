"""empty message

Revision ID: dc378ffad29e
Revises: 89fc4f05c8f2
Create Date: 2018-08-17 16:55:16.997246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc378ffad29e'
down_revision = '89fc4f05c8f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('checkin',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('checked_at', sa.DateTime(), nullable=True),
    sa.Column('checked_in', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('participants',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('firstname', sa.String(), nullable=True),
    sa.Column('lastname', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('affil', sa.String(), nullable=True),
    sa.Column('mobile', sa.String(), nullable=True),
    sa.Column('delivery_address', sa.String(), nullable=True),
    sa.Column('position_type', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('registrations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('registered_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('registrations')
    op.drop_table('participants')
    op.drop_table('checkin')
    # ### end Alembic commands ###
