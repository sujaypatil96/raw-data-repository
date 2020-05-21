"""modify workspace columns types

Revision ID: 87f2810ac800
Revises: 31d9bc8bcc95
Create Date: 2020-05-14 14:36:57.623457

"""
from alembic import op
import sqlalchemy as sa
import rdr_service.model.utils
from sqlalchemy.dialects import mysql

from rdr_service.participant_enums import PhysicalMeasurementsStatus, QuestionnaireStatus, OrderStatus
from rdr_service.participant_enums import WithdrawalStatus, WithdrawalReason, SuspensionStatus, QuestionnaireDefinitionStatus
from rdr_service.participant_enums import EnrollmentStatus, Race, SampleStatus, OrganizationType, BiobankOrderStatus
from rdr_service.participant_enums import OrderShipmentTrackingStatus, OrderShipmentStatus
from rdr_service.participant_enums import MetricSetType, MetricsKey, GenderIdentity
from rdr_service.model.base import add_table_history_table, drop_table_history_table
from rdr_service.model.code import CodeType
from rdr_service.model.site_enums import SiteStatus, EnrollingStatus, DigitalSchedulingStatus, ObsoleteStatus

# revision identifiers, used by Alembic.
revision = '87f2810ac800'
down_revision = '31d9bc8bcc95'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()



def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('ALTER TABLE rdr.workbench_workspace_snapshot MODIFY scientific_approaches TEXT;')
    op.execute('ALTER TABLE rdr.workbench_workspace_snapshot MODIFY intend_to_study TEXT;')
    op.execute('ALTER TABLE rdr.workbench_workspace_snapshot MODIFY findings_from_study TEXT;')
    op.execute('ALTER TABLE rdr.workbench_workspace_approved MODIFY scientific_approaches TEXT;')
    op.execute('ALTER TABLE rdr.workbench_workspace_approved MODIFY intend_to_study TEXT;')
    op.execute('ALTER TABLE rdr.workbench_workspace_approved MODIFY findings_from_study TEXT;')
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
