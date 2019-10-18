"""add columns to genomic_set_member

Revision ID: 5a1b1f7b4761
Revises: f3fdb9d05ab3
Create Date: 2019-09-17 16:06:00.824574

"""
from alembic import op
import sqlalchemy as sa
import model.utils
from sqlalchemy.dialects import mysql

from participant_enums import PhysicalMeasurementsStatus, QuestionnaireStatus, OrderStatus
from participant_enums import WithdrawalStatus, WithdrawalReason, SuspensionStatus, QuestionnaireDefinitionStatus
from participant_enums import EnrollmentStatus, Race, SampleStatus, OrganizationType, BiobankOrderStatus
from participant_enums import OrderShipmentTrackingStatus, OrderShipmentStatus
from participant_enums import MetricSetType, MetricsKey, GenderIdentity
from model.base import add_table_history_table, drop_table_history_table
from model.code import CodeType
from model.site_enums import SiteStatus, EnrollingStatus, DigitalSchedulingStatus, ObsoleteStatus

# revision identifiers, used by Alembic.
revision = '5a1b1f7b4761'
down_revision = 'f3fdb9d05ab3'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()



def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('genomic_set_member', sa.Column('sample_id', sa.String(length=80), nullable=True))
    op.add_column('genomic_set_member', sa.Column('sample_type', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('genomic_set_member', 'sample_type')
    op.drop_column('genomic_set_member', 'sample_id')
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
