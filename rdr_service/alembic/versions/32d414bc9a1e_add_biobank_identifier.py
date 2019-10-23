"""add_biobank_identifier

Revision ID: 32d414bc9a1e
Revises: 9b93d00a35cc
Create Date: 2018-01-30 11:12:24.111826

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "32d414bc9a1e"
down_revision = "9b93d00a35cc"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("biobank_stored_sample", sa.Column("biobank_order_identifier", sa.String(length=80), nullable=False))
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("biobank_stored_sample", "biobank_order_identifier")
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###