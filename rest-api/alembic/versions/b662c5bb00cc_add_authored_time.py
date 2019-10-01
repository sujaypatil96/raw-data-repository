"""add authored time

Revision ID: b662c5bb00cc
Revises: d1f67196215e
Create Date: 2019-05-16 15:43:49.473126

"""
from alembic import op
import sqlalchemy as sa
import model.utils
from sqlalchemy.dialects import mysql


from participant_enums import PhysicalMeasurementsStatus, QuestionnaireStatus, OrderStatus
from participant_enums import WithdrawalStatus, WithdrawalReason, SuspensionStatus, QuestionnaireDefinitionStatus
from participant_enums import EnrollmentStatus, Race, SampleStatus, OrganizationType, BiobankOrderStatus
from participant_enums import OrderShipmentTrackingStatus, OrderShipmentStatus
from participant_enums import MetricSetType, MetricsKey
from model.base import add_table_history_table, drop_table_history_table
from model.code import CodeType
from model.site_enums import SiteStatus, EnrollingStatus, DigitalSchedulingStatus, ObsoleteStatus

# revision identifiers, used by Alembic.
revision = 'b662c5bb00cc'
down_revision = 'd1f67196215e'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()



def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('patient_status', sa.Column('authored', model.utils.UTCDateTime(), nullable=True))
    op.add_column('patient_status', sa.Column('site_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'patient_status', 'site', ['site_id'], ['site_id'])
    op.add_column('patient_status', sa.Column('user', sa.String(length=80), nullable=False))
    op.create_index(op.f('ix_patient_status_organization_id'), 'patient_status', ['organization_id'], unique=False)
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_patient_status_organization_id'), table_name='patient_status')
    op.drop_column('patient_status', 'user')
    op.drop_constraint(None, 'patient_status', type_='foreignkey')
    op.drop_column('patient_status', 'site_id')
    op.drop_column('patient_status', 'authored')
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
