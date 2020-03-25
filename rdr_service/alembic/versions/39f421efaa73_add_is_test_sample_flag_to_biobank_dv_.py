"""Add is_test_sample flag to biobank_dv_order

Revision ID: 39f421efaa73
Revises: 9cbaee181bc9
Create Date: 2020-03-17 12:13:52.824158

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '39f421efaa73'
down_revision = '9cbaee181bc9'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('biobank_dv_order', sa.Column('is_test_sample', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('biobank_dv_order', 'is_test_sample')
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

