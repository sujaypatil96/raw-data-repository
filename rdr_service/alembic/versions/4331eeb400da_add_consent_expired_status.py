"""add consent expired status

Revision ID: 4331eeb400da
Revises: 1c35e6439d1c
Create Date: 2020-07-10 11:54:45.714491

"""
from alembic import op
import sqlalchemy as sa
import rdr_service.model.utils

from rdr_service.participant_enums import ConsentExpireStatus

# revision identifiers, used by Alembic.
revision = '4331eeb400da'
down_revision = '1c35e6439d1c'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('participant_summary', sa.Column('ehr_consent_expire_status',
                                                   rdr_service.model.utils.Enum(ConsentExpireStatus), nullable=True))
    op.add_column('participant_summary', sa.Column('ehr_consent_expire_time',
                                                   rdr_service.model.utils.UTCDateTime(), nullable=True))
    op.add_column('participant_summary', sa.Column('ehr_consent_expire_authored',
                                                   rdr_service.model.utils.UTCDateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('participant_summary', 'ehr_consent_expire_authored')
    op.drop_column('participant_summary', 'ehr_consent_expire_time')
    op.drop_column('participant_summary', 'ehr_consent_expire_status')
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
