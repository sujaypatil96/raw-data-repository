import datetime

from dateutil import parser, tz
from sqlalchemy import desc, func

from rdr_service import config
from rdr_service.dao.base_dao import UpsertableDao
from rdr_service.model.bigquery_sync import BigQuerySync
from rdr_service.model.bq_base import BQRecord
from rdr_service.model.bq_participant_summary import BQModuleStatusEnum, BQParticipantSummarySchema, \
  BQStreetAddressTypeEnum
from rdr_service.model.code import Code
from rdr_service.model.hpo import HPO
from rdr_service.model.measurements import PhysicalMeasurements, PhysicalMeasurementsStatus
from rdr_service.model.organization import Organization
from rdr_service.model.participant import Participant
from rdr_service.model.questionnaire import QuestionnaireConcept
from rdr_service.model.questionnaire_response import QuestionnaireResponse
from rdr_service.model.site import Site
from rdr_service.participant_enums import BiobankOrderStatus, EnrollmentStatus, SampleStatus, \
  SuspensionStatus, \
  WithdrawalReason, WithdrawalStatus


class BigQuerySyncDao(UpsertableDao):

  def __init__(self):
    super(BigQuerySyncDao, self).__init__(BigQuerySync)


class BQParticipantSummaryGenerator(object):
  """
  Generate a Participant Summary BQRecord object
  """
  dao = None

  def _update_schema(self, dict1, dict2):
    """
    Safely add dict2 schema to to dict1 schema
    :param dict1: dict object
    :param dict2: dict object
    :return: dict
    """
    lists = {key: val for key, val in dict1.iteritems()}
    dict1.update(dict2)
    for key, val in lists.iteritems():  # pylint: disable=unused-variable
      if key in dict2:
        # This assumes all sub-tables are set to repeated (multi-row) type.
        dict1[key] = lists[key] + dict2[key]

    return dict1

  def make_participant_summary(self, p_id, convert_to_enum=False):
    """
    Build a Participant Summary BQRecord object for the given participant id.
    :param p_id: participant id
    :param convert_to_enums: If schema field description includes Enum class info, convert value to Enum.
    :return: BQRecord object
    """
    if not self.dao:
      self.dao = BigQuerySyncDao()

    with self.dao.session() as session:
      # prep participant info from Participant record
      summary = self._prep_participant(p_id, session)
      # prep ConsentPII questionnaire information
      summary = self._update_schema(summary, self._prep_consentpii_answers(p_id, session))
      # prep questionnaire modules information, includes gathering extra consents.
      summary = self._update_schema(summary, self._prep_modules(p_id, session))
      # prep physical measurements
      summary = self._update_schema(summary, self._prep_physical_measurements(p_id, session))
      # prep race and gender
      summary = self._update_schema(summary, self._prep_the_basics(p_id, session))
      # prep biobank orders and samples
      summary = self._update_schema(summary, self._prep_biobank_info(p_id, session))
      # calculate enrollment status for participant
      summary = self._update_schema(summary, self._calculate_enrollment_status(summary))
      # calculate distinct visits
      summary = self._update_schema(summary, self._calculate_distinct_visits(summary))

      return BQRecord(schema=BQParticipantSummarySchema, data=summary, convert_to_enum=convert_to_enum)

  def save_participant_summary(self, p_id, bqrecord):
    """
    Save the BQRecord object into the bigquery_sync table.
    :param p_id: participant id
    :param bqrecord: BQRecord object
    """
    if not self.dao:
      self.dao = BigQuerySyncDao()

    with self.dao.session() as session:

      bqs_rec = session.query(BigQuerySync.id).filter(BigQuerySync.participantId == p_id).first()

      bqs = BigQuerySync()
      bqs.id = bqs_rec.id if bqs_rec else None
      bqs.participantId = p_id
      bqs.dataSet = 'rdr_ops_data_view'
      bqs.table = 'participant_summary'
      bqs.resource = bqrecord.to_json()
      self.dao.upsert_with_session(session, bqs)

  def _lookup_code_value(self, code_id, session):
    """
    Return the code id string value from the code table.
    :param code_id: codeId from code table
    :param session: DAO session object
    :return: string
    """
    if code_id is None:
      return None
    result = session.query(Code.value).filter(Code.codeId == int(code_id)).first()
    if not result:
      return None
    return result.value

  def _lookup_code_id(self, code, session):
    """
    Return the code id for the given code value string.
    :param code: code value string
    :param session: DAO session object
    :return: int
    """
    if code is None:
      return None
    result = session.query(Code.codeId).filter(Code.value == code).first()
    if not result:
      return None
    return result.codeId

  def _lookup_site_name(self, site_id, session):
    """
    Look up the site name
    :param site_id: site id integer
    :param session: DAO session object
    :return: string
    """
    site = session.query(Site.googleGroup).filter(Site.siteId == site_id).first()
    if not site:
      return None
    return site.googleGroup

  def _prep_participant(self, p_id, session):
    """
    Get the information from the participant record
    :param p_id: participant id
    :param session: DAO session object
    :return: dict
    """
    p = session.query(Participant).filter(Participant.participantId == p_id).first()
    if not p:
      raise LookupError('participant lookup for P{0} failed.'.format(p_id))

    hpo = session.query(HPO.name).filter(HPO.hpoId == p.hpoId).first()
    organization = session.query(Organization.externalId). \
                          filter(Organization.organizationId == p.organizationId).first()


    withdrawal_status = WithdrawalStatus(p.withdrawalStatus)
    withdrawal_reason = WithdrawalReason(p.withdrawalReason if p.withdrawalReason else 0)
    suspension_status = SuspensionStatus(p.suspensionStatus)

    data = {
      'participant_id': p_id,
      'biobank_id': p.biobankId,
      'last_modified': p.lastModified,
      'sign_up_time': p.signUpTime,
      'hpo': hpo.name if hpo else None,
      'hpo_id': p.hpoId,
      'organization': organization.externalId if organization else None,
      'organization_id': p.organizationId,

      'withdrawal_status': str(withdrawal_status),
      'withdrawal_status_id': int(withdrawal_status),
      'withdrawal_reason': str(withdrawal_reason),
      'withdrawal_reason_id': int(withdrawal_reason),
      'withdrawal_time': p.withdrawalTime,
      'withdrawal_authored': p.withdrawalAuthored,
      'withdrawal_reason_justification': p.withdrawalReasonJustification,

      'suspension_status': str(suspension_status),
      'suspension_status_id': int(suspension_status),
      'suspension_time': p.suspensionTime,

      'site': self._lookup_site_name(p.siteId, session),
      'site_id': p.siteId,
      'is_ghost_id': 1 if p.isGhostId is True else 0
    }

    return data

  def _prep_consentpii_answers(self, p_id, session):
    """
    Get participant information from the ConsentPII questionnaire
    :param p_id: participant id
    :param session: DAO session object
    :return: dict
    """
    qnans = self.dao.call_proc('sp_get_questionnaire_answers', args=['ConsentPII', p_id])
    if not qnans or len(qnans) == 0:
      # return the minimum data required when we don't have the questionnaire data.
      return {'email': None, 'is_ghost_id': 0}
    qnan = BQRecord(schema=None, data=qnans[0])  # use only most recent questionnaire.

    data = {
      'first_name': qnan.PIIName_First,
      'middle_name': qnan.PIIName_Middle,
      'last_name': qnan.PIIName_Last,
      'date_of_birth': qnan.PIIBirthInformation_BirthDate,
      'language': self._lookup_code_value(qnan.Language_SpokenWrittenLanguage, session),
      'language_id': qnan.Language_SpokenWrittenLanguage,
      'primary_language': qnan.language,
      'email': qnan.ConsentPII_EmailAddress,
      'phone_number': qnan.PIIContactInformation_Phone,
      'login_phone_number': qnan.ConsentPII_VerifiedPrimaryPhoneNumber,
      'contact_method': self._lookup_code_value(qnan.PIIContactInformation_RecontactMethod, session),
      'contact_method_id': qnan.PIIContactInformation_RecontactMethod,
      'addresses': [
        {
          'addr_type': BQStreetAddressTypeEnum.RESIDENCE.name,
          'addr_type_id': BQStreetAddressTypeEnum.RESIDENCE.value,
          'addr_street_address_1': qnan.PIIAddress_StreetAddress,
          'addr_street_address_2': qnan.PIIAddress_StreetAddress2,
          'addr_city': qnan.StreetAddress_PIICity,
          'addr_state': qnan.StreetAddress_PIIState.replace('PIIState_', '').upper()
                          if qnan.StreetAddress_PIIState else None,
          'addr_zip': qnan.StreetAddress_PIIZIP,
          'addr_country': 'us'
        }
      ],
      'consents': [
        {
          'consent': 'ConsentPII',
          'consent_id': self._lookup_code_id('ConsentPII', session),
          'consent_date': parser.parse(qnan.authored).date() if qnan.authored else None,
          'consent_value': 'ConsentPermission_Yes',
          'consent_value_id': self._lookup_code_id('ConsentPermission_Yes', session),
        },
        {
          'consent': 'ExtraConsent_CABoRSignature',
          'consent_id': self._lookup_code_id('ExtraConsent_CABoRSignature', session),
          'consent_date': parser.parse(qnan.authored).date() if qnan.authored else None,
          'consent_value': qnan.ExtraConsent_CABoRSignature,
          'consent_value_id': self._lookup_code_id(qnan.ExtraConsent_CABoRSignature, session),
        }
      ]
    }

    return data

  def _prep_modules(self, p_id, session):
    """
    Find all questionnaire modules the participant has completed and loop through them.
    :param p_id: participant id
    :param session: DAO session object
    :return: dict
    """
    code_id_query = session.query(func.max(QuestionnaireConcept.codeId)).\
                        filter(QuestionnaireResponse.questionnaireId ==
                                QuestionnaireConcept.questionnaireId).label('codeId')
    query = session.query(
                  QuestionnaireResponse.questionnaireResponseId, QuestionnaireResponse.authored,
                  QuestionnaireResponse.created, QuestionnaireResponse.language, code_id_query).\
                filter(QuestionnaireResponse.participantId == p_id).\
                order_by(QuestionnaireResponse.questionnaireResponseId)
    # sql = self.dao.query_to_text(query)
    results = query.all()

    data = dict()
    modules = list()
    consents = list()
    baseline_modules = ['TheBasics', 'OverallHealth', 'Lifestyle']
    try:
      baseline_modules = config.getSettingList('baseline_ppi_questionnaire_fields')
    except ValueError:
      pass
    except AssertionError:  # unittest errors because of GCP SDK
      pass

    consent_modules = {
      # module: question code string
      'DVEHRSharing': 'DVEHRSharing_AreYouInterested',
      'EHRConsentPII': 'EHRConsentPII_ConsentPermission',
    }

    if results:
      for row in results:
        module_name = self._lookup_code_value(row.codeId, session)
        modules.append({
          'mod_module': module_name,
          'mod_baseline_module': 'true' if module_name in baseline_modules else 'false',
          'mod_authored': row.authored,
          'mod_created': row.created,
          'mod_language': row.language,
          'mod_status': BQModuleStatusEnum.SUBMITTED.name,
          'mod_status_id': BQModuleStatusEnum.SUBMITTED.value,
        })

        # check if this is a module with consents.
        if module_name not in consent_modules:
          continue
        qnans = self.dao.call_proc('sp_get_questionnaire_answers', args=[module_name, p_id])
        if qnans and len(qnans) > 0:
          qnan = BQRecord(schema=None, data=qnans[0])  # use only most recent questionnaire.
          consents.append({
            'consent': consent_modules[module_name],
            'consent_id': self._lookup_code_id(consent_modules[module_name], session),
            'consent_date': parser.parse(qnan.authored).date() if qnan.authored else None,
            'consent_value': qnan[consent_modules[module_name]],
            'consent_value_id': self._lookup_code_id(qnan[consent_modules[module_name]], session),
          })

    if len(modules) > 0:
      data['modules'] = modules
      if len(consents) > 0:
        data['consents'] = consents

    return data

  def _prep_the_basics(self, p_id, session):
    """
    Get the participant's race and gender selections
    :param p_id: participant id
    :param session: DAO session object
    :return: dict
    """
    qnans = self.dao.call_proc('sp_get_questionnaire_answers', args=['TheBasics', p_id])
    if not qnans or len(qnans) == 0:
      return {}

    # get race question answers
    qnan = BQRecord(schema=None, data=qnans[0])  # use only most recent questionnaire.
    data = {}
    if qnan.Race_WhatRaceEthnicity:
      rl = list()
      for val in qnan.Race_WhatRaceEthnicity.split(','):
        rl.append({'race': val, 'race_id': self._lookup_code_id(val, session)})
      data['races'] = rl
    # get gender question answers
    gl = list()
    if qnan.Gender_GenderIdentity:
      for val in qnan.Gender_GenderIdentity.split(','):
        if val == 'GenderIdentity_AdditionalOptions':
          continue
        gl.append({'gender': val, 'gender_id': self._lookup_code_id(val, session)})
    # get additional gender answers, if any.
    if qnan.GenderIdentity_SexualityCloserDescription:
      for val in qnan.GenderIdentity_SexualityCloserDescription.split(','):
        gl.append({'gender': val, 'gender_id': self._lookup_code_id(val, session)})

    if len(gl) > 0:
      data['genders'] = gl

    data['education'] = qnan.EducationLevel_HighestGrade
    data['education_id'] = self._lookup_code_id(qnan.EducationLevel_HighestGrade, session)
    data['income'] = qnan.Income_AnnualIncome
    data['income_id'] = self._lookup_code_id(qnan.Income_AnnualIncome, session)
    data['sex'] = qnan.BiologicalSexAtBirth_SexAtBirth
    data['sex_id'] = self._lookup_code_id(qnan.BiologicalSexAtBirth_SexAtBirth, session)
    data['sexual_orientation'] = qnan.TheBasics_SexualOrientation
    data['sexual_orientation_id'] = self._lookup_code_id(qnan.TheBasics_SexualOrientation, session)

    return data

  def _prep_physical_measurements(self, p_id, session):
    """
    Get participant's physical measurements information
    :param p_id: participant id
    :param session: DAO session object
    :return: dict
    """
    data = {}
    pm_list = list()

    query = session.query(PhysicalMeasurements.created, PhysicalMeasurements.createdSiteId, PhysicalMeasurements.final,
                       PhysicalMeasurements.finalized, PhysicalMeasurements.finalizedSiteId,
                       PhysicalMeasurements.status).\
            filter(PhysicalMeasurements.participantId == p_id).\
            order_by(desc(PhysicalMeasurements.created))
    # sql = self.dao.query_to_text(query)
    results = query.all()

    for row in results:
      pm_list.append({
        'pm_status': str(PhysicalMeasurementsStatus(row.status) if row.status else PhysicalMeasurementsStatus.UNSET),
        'pm_status_id': int(PhysicalMeasurementsStatus(row.status) if row.status else
                                PhysicalMeasurementsStatus.UNSET),
        'pm_created': row.created,
        'pm_created_site': self._lookup_site_name(row.createdSiteId, session),
        'pm_created_site_id': row.createdSiteId,
        'pm_finalized': row.finalized,
        'pm_finalized_site': self._lookup_site_name(row.finalizedSiteId, session),
        'pm_finalized_site_id': row.finalizedSiteId,
      })

    if len(pm_list) > 0:
      data['pm'] = pm_list
    return data

  def _prep_biobank_info(self, p_id, session):
    """
    Look up biobank orders
    :param p_id: participant id
    :param session: DAO session object
    :return:
    """
    data = {}
    orders = list()
    baseline_tests = ["1ED04", "1ED10", "1HEP4", "1PST8", "2PST8", "1SST8", "2SST8",
                      "1PS08", "1SS08", "1UR10", "1CFD9", "1PXR2", "1UR90", "2ED10"]
    try:
      baseline_tests = config.getSettingList('baseline_sample_test_codes')
    except ValueError:
      pass
    except AssertionError:  # unittest errors because of GCP SDK
      pass

    dna_tests = ["1ED10", "2ED10", "1ED04", "1SAL", "1SAL2"]
    try:
      dna_tests = config.getSettingList('dna_sample_test_codes')
    except ValueError:
      pass
    except AssertionError:  # unittest errors because of GCP SDK
      pass

    sql = """
      select bo.biobank_order_id, bo.created, bo.collected_site_id, bo.processed_site_id, bo.finalized_site_id, 
              bos.test, bos.collected, bos.processed, bos.finalized, bo.order_status,
              bss.confirmed as bb_confirmed, bss.created as bb_created, bss.disposed as bb_disposed, 
              bss.status as bb_status, (
                select count(1) from biobank_dv_order bdo where bdo.biobank_order_id = bo.biobank_order_id
              ) as dv_order
        from biobank_order bo inner join biobank_ordered_sample bos on bo.biobank_order_id = bos.order_id
                inner join biobank_order_identifier boi on bo.biobank_order_id = boi.biobank_order_id
                left outer join 
                  biobank_stored_sample bss on boi.`value` = bss.biobank_order_identifier and bos.test = bss.test
        where boi.`system` = 'https://www.pmi-ops.org' and bo.participant_id = :pid
        order by bo.biobank_order_id, bos.test;
    """

    cursor = session.execute(sql, {'pid': p_id})
    results = [r for r in cursor]
    # loop through results and create one order record for each biobank_order_id value.
    for row in results:
      if not filter(lambda order: order['bbo_biobank_order_id'] == row.biobank_order_id, orders):
        orders.append({
          'bbo_biobank_order_id': row.biobank_order_id,
          'bbo_created': row.created,
          'bbo_status': str(BiobankOrderStatus(row.order_status) if row.order_status else BiobankOrderStatus.UNSET),
          'bbo_status_id': int(BiobankOrderStatus(row.order_status) if row.order_status else BiobankOrderStatus.UNSET),
          'bbo_dv_order': 'false' if row.dv_order == 0 else 'true',
          'bbo_collected_site': self._lookup_site_name(row.collected_site_id, session),
          'bbo_collected_site_id': row.collected_site_id,
          'bbo_processed_site': self._lookup_site_name(row.processed_site_id, session),
          'bbo_processed_site_id': row.processed_site_id,
          'bbo_finalized_site': self._lookup_site_name(row.finalized_site_id, session),
          'bbo_finalized_site_id': row.finalized_site_id,
        })
    # loop through results again and add each sample to it's order.
    for row in results:
      # get the order list index for this sample record
      idx = orders.index(filter(lambda order: order['bbo_biobank_order_id'] == row.biobank_order_id, orders)[0])
      # if we haven't added any samples to this order, create an empty list.
      if 'samples' not in orders[idx]:
        orders[idx]['bbo_samples'] = list()
      # append the sample to the order
      orders[idx]['bbo_samples'].append({
        'bbs_test': row.test,
        'bbs_baseline_test': 'true' if row.test in baseline_tests else 'false',
        'bbs_dna_test': 'true' if row.test in dna_tests else 'false',
        'bbs_collected': row.collected,
        'bbs_processed': row.processed,
        'bbs_finalized': row.finalized,
        'bbs_confirmed': row.bb_confirmed,
        'bbs_status': str(SampleStatus.RECEIVED) if row.bb_confirmed else None,
        'bbs_status_id': int(SampleStatus.RECEIVED) if row.bb_confirmed else None,
        'bbs_created': row.bb_created,
        'bbs_disposed': row.bb_disposed,
        'bbs_disposed_reason': str(SampleStatus(row.bb_status)) if row.bb_status else None,
        'bbs_disposed_reason_id': int(SampleStatus(row.bb_status)) if row.bb_status else None,
      })

    if len(orders) > 0:
      data['biobank_orders'] = orders
    return data

  def _calculate_enrollment_status(self, summary):
    """
    Calculate the participant's enrollment status
    :param summary: summary data
    :return: dict
    """
    if 'consents' not in summary:
      return {}
    try:
      baseline_modules = config.getSettingList('baseline_ppi_questionnaire_fields')
    except ValueError:
      baseline_modules = ['TheBasics', 'OverallHealth', 'Lifestyle']

    study_consent = ehr_consent = dvehr_consent = pm_complete = False
    status = None
    # iterate over consents
    for consent in summary['consents']:
      if consent['consent'] == 'ConsentPII':
        study_consent = True
      if consent['consent'] == 'EHRConsentPII_ConsentPermission' and \
                            consent['consent_value'] == 'ConsentPermission_Yes':
        ehr_consent = True
      if consent['consent'] == 'DVEHRSharing_AreYouInterested' and \
                            consent['consent_value'] == 'DVEHRSharing_Yes':
        dvehr_consent = True

    # check physical measurements
    if 'pm_status_id' in summary and summary['pm_status_id'] == int(PhysicalMeasurementsStatus.COMPLETED):
      pm_complete = True

    baseline_module_count = dna_sample_count = 0
    if 'modules' in summary:
      baseline_module_count = len(filter(lambda module: module['mod_baseline_module'] == 'true', summary['modules']))
    if 'biobank_orders' in summary:
      for order in summary['biobank_orders']:
        if 'samples' in order:
          dna_sample_count += len(filter(lambda sample: sample['bbs_dna_test'] == 'true', order['samples']))

    if study_consent:
      status = EnrollmentStatus.INTERESTED
    if ehr_consent or dvehr_consent:
      status = EnrollmentStatus.MEMBER
    if pm_complete and 'modules' in summary and baseline_module_count == len(baseline_modules) and \
            dna_sample_count > 0:
      status = EnrollmentStatus.FULL_PARTICIPANT

    data = {
      'enrollment_status': str(status) if status else None,
      'enrollment_status_id': int(status) if status else None,
    }
    return data

  def _calculate_distinct_visits(self, summary):  # pylint: disable=unused-argument
    """
    Calculate the distinct number of visits.
    :param summary: summary data
    :return: dict
    """
    def datetime_to_date(val):
      """
      Change from UTC to middle of the US before extracting date. That way if we have an early and late visit
      they will end up as the same day.
      """
      tmp = val.replace(tzinfo=tz.tzutc()).astimezone(tz.gettz('America/Denver'))
      return datetime.date(tmp.year, tmp.month, tmp.day)

    data = {}
    dates = list()

    if 'pm' in summary:
      for pm in summary['pm']:
        if pm['pm_status_id'] != int(PhysicalMeasurementsStatus.CANCELLED) and pm['pm_finalized']:
          dates.append(datetime_to_date(pm['pm_finalized']))

    if 'biobank_orders' in summary:
      for order in summary['biobank_orders']:
        if order['bbo_status_id'] != int(BiobankOrderStatus.CANCELLED) and 'bbo_samples' in order:
          for sample in order['bbo_samples']:
            if 'bbs_finalized' in sample and sample['bbs_finalized'] and \
                              isinstance(sample['bbs_finalized'], datetime.datetime):
              dates.append(datetime_to_date(sample['bbs_finalized']))

    dates = list(set(dates))  # de-dup list
    data['distinct_visits'] = len(dates)
    return data


def deferred_bq_participant_summary_update(p_id):
  """
  Deferred task to update the Participant Summary record for the given participant.
  :param p_id: Participant ID
  """
  gen = BQParticipantSummaryGenerator()
  gen.save_participant_summary(p_id, gen.make_participant_summary(p_id))