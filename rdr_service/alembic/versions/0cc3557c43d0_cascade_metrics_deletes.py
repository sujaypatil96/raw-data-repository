"""Cascade metrics deletes

Revision ID: 0cc3557c43d0
Revises: 3d4a6433e26d
Create Date: 2017-05-04 11:28:25.951742

"""
from alembic import op
import sqlalchemy as sa
import model.utils


from rdr_service.participant_enums import PhysicalMeasurementsStatus, QuestionnaireStatus
from rdr_service.participant_enums import WithdrawalStatus, SuspensionStatus
from rdr_service.participant_enums import EnrollmentStatus, Race, SampleStatus, OrganizationType
from rdr_service.model.code import CodeType

# revision identifiers, used by Alembic.
revision = '0cc3557c43d0'
down_revision = '3d4a6433e26d'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###



def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'metrics_bucket_ibfk_1', 'metrics_bucket', type_='foreignkey')
    op.create_foreign_key(None, 'metrics_bucket', 'metrics_version', ['metrics_version_id'], ['metrics_version_id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'metrics_bucket', type_='foreignkey')
    op.create_foreign_key(u'metrics_bucket_ibfk_1', 'metrics_bucket', 'metrics_version', ['metrics_version_id'], ['metrics_version_id'])
    # ### end Alembic commands ###