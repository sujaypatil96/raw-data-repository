"""raw_export_api

Revision ID: 32df5fa890bf
Revises: 0e0908363f40
Create Date: 2018-05-15 12:42:12.407203

"""
from alembic import op
import sqlalchemy as sa
import model.utils


from rdr_service.participant_enums import PhysicalMeasurementsStatus, QuestionnaireStatus, OrderStatus
from rdr_service.participant_enums import WithdrawalStatus, SuspensionStatus
from rdr_service.participant_enums import EnrollmentStatus, Race, SampleStatus, OrganizationType
from rdr_service.participant_enums import MetricSetType, MetricsKey
from rdr_service.model.site_enums import SiteStatus, EnrollingStatus
from rdr_service.model.code import CodeType

# revision identifiers, used by Alembic.
revision = '32df5fa890bf'
down_revision = '0e0908363f40'
branch_labels = None
depends_on = None

_RAW_QUESTIONNAIRE_RESPONSE_VIEW_EXPORT_SQL = """
CREATE OR REPLACE VIEW raw_questionnaire_response_answer_view AS
 SELECT
   p.participant_id participant_id,
   ps.last_name,
   ps.first_name,
   ps.email,
   p.sign_up_time,
   p.suspension_status participant_suspension_status,
   p.suspension_time,
   hpo.name hpo,
   (SELECT GROUP_CONCAT(concept_code.value SEPARATOR ',') FROM questionnaire_concept qc
     INNER JOIN code concept_code ON concept_code.code_id = qc.code_id
     WHERE qc.questionnaire_id = q.questionnaire_id) module,
   q.questionnaire_id questionnaire_id,
   qr.questionnaire_response_id questionnaire_response_id,
   qr.created,
   qc.value question_code,
   qc.code_id question_code_id,
   qra.end_time,
   ac.value answer_code,
   ac.code_id answer_code_id,
   qra.value_boolean answer_boolean,
   qra.value_decimal,
   qra.value_integer,
   qra.value_string,
   qra.value_date,
   qra.value_datetime,
   qra.value_uri
 FROM
   participant p
    INNER JOIN questionnaire_response qr ON p.participant_id = qr.participant_id
    INNER JOIN questionnaire_response_answer qra
       ON qra.questionnaire_response_id = qr.questionnaire_response_id
    INNER JOIN questionnaire_question qq ON qra.question_id = qq.questionnaire_question_id
    INNER JOIN questionnaire q ON qq.questionnaire_id = q.questionnaire_id
    INNER JOIN code qc ON qq.code_id = qc.code_id
    INNER JOIN participant_summary ps ON p.participant_id = ps.participant_id
    LEFT OUTER JOIN hpo ON p.hpo_id = hpo.hpo_id
    LEFT OUTER JOIN code ac ON qra.value_code_id = ac.code_id
    WHERE p.withdrawal_status = 1 AND # NOT_WITHDRAWN
        (ps.email IS NULL OR ps.email NOT LIKE '%@example.com') AND
        (hpo.name IS NULL OR hpo.name != 'TEST') AND
        /* Blacklist any codes which are superfluous for PPI QA. */
        qc.value NOT IN (
          'ExtraConsent_DataSharingVideo',
          'ExtraConsent_EmailACopyToMe',
          'ExtraConsent_FitnessTrackerVideo',
          'ExtraConsent_HealthDataVideo',
          'ExtraConsent_HealthRecordVideo',
          'ExtraConsent_KeepinginTouchVideo',
          'ExtraConsent_OtherHealthDataVideo',
          'ExtraConsent_PhysicalMeausrementsVideo', # Intentional typo
          'ExtraConsent_WelcomeVideo',
          'YoutubeVideos_WhatAreWeAsking',
          'YoutubeVideos_RiskToPrivacy'
        )
"""


_RAW_PHYSICAL_MEASUREMENTS_VIEW_EXPORT_SQL = """
CREATE OR REPLACE VIEW raw_physical_measurements_view AS
 SELECT
   p.participant_id participant_id,
   ps.last_name,
   ps.first_name,
   ps.email,
   p.sign_up_time,
   p.suspension_status participant_suspension_status,
   p.suspension_time,
   pm.physical_measurements_id physical_measurements_id,
   pm.created,
   pm.amended_measurements_id amended_measurements_id,
   pm.created_site_id created_site_id,
   pm.created_username created_username,
   pm.finalized_site_id finalized_site_id,
   pm.finalized_username finalized_username,
   m.measurement_id measurement_id,
   m.code_system code_system,
   m.code_value code_value,
   m.measurement_time,
   m.body_site_code_system body_site_code_system,
   m.body_site_code_value body_site_code_value,
   m.value_string,
   m.value_decimal value_decimal,
   m.value_unit value_unit,
   m.value_code_system value_code_system,
   m.value_code_value value_code_value,
   m.value_datetime,
   m.parent_id parent_id,
   m.qualifier_id qualifier_id
 FROM
   participant p
    INNER JOIN physical_measurements pm
       ON pm.participant_id = p.participant_id
    INNER JOIN measurement m
       ON pm.physical_measurements_id = m.physical_measurements_id
    INNER JOIN participant_summary ps
       ON p.participant_id = ps.participant_id
    LEFT OUTER JOIN hpo
       ON p.hpo_id = hpo.hpo_id
  WHERE p.withdrawal_status = 1 AND # NOT_WITHDRAWN
      (ps.email IS NULL OR ps.email NOT LIKE '%@example.com') AND
      (hpo.name IS NULL OR hpo.name != 'TEST') AND
      pm.final = 1
"""

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()



def upgrade_rdr():
    op.execute(_RAW_QUESTIONNAIRE_RESPONSE_VIEW_EXPORT_SQL)
    op.execute(_RAW_PHYSICAL_MEASUREMENTS_VIEW_EXPORT_SQL)


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
