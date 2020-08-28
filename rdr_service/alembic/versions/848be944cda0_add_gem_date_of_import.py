"""Add gem date of import.

Revision ID: 848be944cda0
Revises: 2c3a71f9fc04
Create Date: 2020-08-28 09:01:29.442539

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '848be944cda0'
down_revision = '2c3a71f9fc04'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('genomic_set_member', sa.Column('gem_date_of_import', sa.DateTime(), nullable=True))
    op.add_column('genomic_set_member_history', sa.Column('gem_date_of_import', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('genomic_set_member', 'gem_date_of_import')
    op.drop_column('genomic_set_member_history', 'gem_date_of_import')
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
