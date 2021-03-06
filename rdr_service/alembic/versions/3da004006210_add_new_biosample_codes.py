"""add new biosample codes

Revision ID: 3da004006210
Revises: c2dd2332a63f
Create Date: 2018-03-01 09:20:45.647001

"""
import model.utils
import sqlalchemy as sa
from alembic import op

from rdr_service.participant_enums import OrderStatus, SampleStatus

# revision identifiers, used by Alembic.
revision = "3da004006210"
down_revision = "c2dd2332a63f"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "participant_summary", sa.Column("sample_order_status_2pst8", model.utils.Enum(OrderStatus), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_order_status_2pst8_time", model.utils.UTCDateTime(), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_order_status_2sst8", model.utils.Enum(OrderStatus), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_order_status_2sst8_time", model.utils.UTCDateTime(), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_status_2pst8", model.utils.Enum(SampleStatus), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_status_2pst8_time", model.utils.UTCDateTime(), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_status_2sst8", model.utils.Enum(SampleStatus), nullable=True)
    )
    op.add_column(
        "participant_summary", sa.Column("sample_status_2sst8_time", model.utils.UTCDateTime(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("participant_summary", "sample_status_2sst8_time")
    op.drop_column("participant_summary", "sample_status_2sst8")
    op.drop_column("participant_summary", "sample_status_2pst8_time")
    op.drop_column("participant_summary", "sample_status_2pst8")
    op.drop_column("participant_summary", "sample_order_status_2sst8_time")
    op.drop_column("participant_summary", "sample_order_status_2sst8")
    op.drop_column("participant_summary", "sample_order_status_2pst8_time")
    op.drop_column("participant_summary", "sample_order_status_2pst8")
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
