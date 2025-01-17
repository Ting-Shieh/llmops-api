"""empty message

Revision ID: d16129dadfc3
Revises: e4b8b6bd829d
Create Date: 2025-01-17 22:27:45.289664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd16129dadfc3'
down_revision = 'e4b8b6bd829d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('app', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=255), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('app', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
