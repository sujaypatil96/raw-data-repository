"""whitelist ppi ints

Revision ID: d2e17663c615
Revises: 106ecd33248b
Create Date: 2018-01-10 14:02:10.393509

"""
from alembic import op
import sqlalchemy as sa
import model.utils


from participant_enums import PhysicalMeasurementsStatus, QuestionnaireStatus, OrderStatus
from participant_enums import WithdrawalStatus, SuspensionStatus
from participant_enums import EnrollmentStatus, Race, SampleStatus, OrganizationType
from participant_enums import MetricSetType, MetricsKey
from model.site_enums import SiteStatus
from model.code import CodeType

# revision identifiers, used by Alembic.
revision = 'd2e17663c615'
down_revision = '106ecd33248b'
branch_labels = None
depends_on = None




def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    pass


def downgrade_rdr():
    pass


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###