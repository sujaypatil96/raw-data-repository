from datetime import datetime
from rdr_service.code_constants import PPI_SYSTEM
from rdr_service.model.api_user import ApiUser
from rdr_service.model.biobank_order import BiobankOrder, BiobankOrderHistory, BiobankOrderedSample,\
    BiobankOrderedSampleHistory, BiobankOrderIdentifier
from rdr_service.model.biobank_stored_sample import BiobankStoredSample
from rdr_service.model.code import Code
from rdr_service.model.deceased_report import DeceasedReport
from rdr_service.model.log_position import LogPosition
from rdr_service.model.hpo import HPO
from rdr_service.model.organization import Organization
from rdr_service.model.participant import Participant, ParticipantHistory
from rdr_service.model.participant_summary import ParticipantSummary
from rdr_service.model.questionnaire import Questionnaire, QuestionnaireConcept, QuestionnaireHistory,\
    QuestionnaireQuestion
from rdr_service.model.questionnaire_response import QuestionnaireResponse, QuestionnaireResponseAnswer
from rdr_service.model.site import Site
from rdr_service.participant_enums import (
    DeceasedNotification,
    DeceasedReportStatus,
    DeceasedStatus,
    EnrollmentStatus,
    SuspensionStatus,
    UNSET_HPO_ID,
    WithdrawalStatus,
)


class DataGenerator:
    def __init__(self, session, faker):
        self.session = session
        self.faker = faker
        self._next_unique_participant_id = 900000000
        self._next_unique_participant_biobank_id = 500000000
        self._next_unique_biobank_order_id = 100000000
        self._next_unique_biobank_stored_sample_id = 800000000
        self._next_unique_questionnaire_response_id = 500000000

    def _commit_to_database(self, model):
        self.session.add(model)
        self.session.commit()

    def create_database_questionnaire(self, **kwargs):
        questionnaire = self._questionnaire(**kwargs)
        self._commit_to_database(questionnaire)
        return questionnaire

    def _questionnaire(self, **kwargs):
        for field, default in [('version', 1),
                               ('created', datetime.now()),
                               ('lastModified', datetime.now()),
                               ('resource', 'test')]:
            if field not in kwargs:
                kwargs[field] = default

        return Questionnaire(**kwargs)

    def create_database_questionnaire_concept(self, **kwargs):
        questionnaire_concept = self._questionnaire_concept(**kwargs)
        self._commit_to_database(questionnaire_concept)
        return questionnaire_concept

    def _questionnaire_concept(self, **kwargs):
        return QuestionnaireConcept(**kwargs)

    def create_database_questionnaire_history(self, **kwargs):
        questionnaire_history = self._questionnaire_history(**kwargs)
        self._commit_to_database(questionnaire_history)
        return questionnaire_history

    def _questionnaire_history(self, **kwargs):
        for field, default in [('version', 1),
                               ('created', datetime.now()),
                               ('lastModified', datetime.now()),
                               ('resource', 'test')]:
            if field not in kwargs:
                kwargs[field] = default

        if 'questionnaireId' not in kwargs:
            questionnaire = self.create_database_questionnaire()
            kwargs['questionnaireId'] = questionnaire.questionnaireId

        return QuestionnaireHistory(**kwargs)

    def create_database_questionnaire_response_answer(self, **kwargs):
        questionnaire_response_answer = self._questionnaire_response_answer(**kwargs)
        self._commit_to_database(questionnaire_response_answer)
        return questionnaire_response_answer

    def _questionnaire_response_answer(self, **kwargs):
        return QuestionnaireResponseAnswer(**kwargs)

    def create_database_questionnaire_response(self, **kwargs):
        questionnaire_response = self._questionnaire_response(**kwargs)
        self._commit_to_database(questionnaire_response)
        return questionnaire_response

    def _questionnaire_response(self, **kwargs):
        for field, default in [('created', datetime.now()),
                               ('resource', 'test')]:
            if field not in kwargs:
                kwargs[field] = default

        if 'questionnaireResponseId' not in kwargs:
            kwargs['questionnaireResponseId'] = self.unique_questionnaire_response_id()

        return QuestionnaireResponse(**kwargs)

    def create_database_questionnaire_question(self, **kwargs):
        questionnaire_question = self._questionnaire_question(**kwargs)
        self._commit_to_database(questionnaire_question)
        return questionnaire_question

    def _questionnaire_question(self, **kwargs):
        if 'repeats' not in kwargs:
            kwargs['repeats'] = True

        return QuestionnaireQuestion(**kwargs)

    def unique_participant_id(self):
        next_participant_id = self._next_unique_participant_id
        self._next_unique_participant_id += 1
        return next_participant_id

    def unique_participant_biobank_id(self):
        next_biobank_id = self._next_unique_participant_biobank_id
        self._next_unique_participant_biobank_id += 1
        return next_biobank_id

    def unique_biobank_order_id(self):
        next_biobank_order_id = self._next_unique_biobank_order_id
        self._next_unique_biobank_order_id += 1
        return next_biobank_order_id

    def unique_biobank_stored_sample_id(self):
        next_biobank_stored_sameple_id = self._next_unique_biobank_stored_sample_id
        self._next_unique_biobank_stored_sample_id += 1
        return next_biobank_stored_sameple_id

    def unique_questionnaire_response_id(self):
        next_questionnaire_response_id = self._next_unique_questionnaire_response_id
        self._next_unique_questionnaire_response_id += 1
        return next_questionnaire_response_id

    def create_database_site(self, **kwargs):
        site = self._site_with_defaults(**kwargs)
        self._commit_to_database(site)
        return site

    def _site_with_defaults(self, **kwargs):
        defaults = {
            'siteName': 'example_site'
        }
        defaults.update(kwargs)
        return Site(**defaults)

    def create_database_organization(self, **kwargs):
        organization = self._organization_with_defaults(**kwargs)
        self._commit_to_database(organization)
        return organization

    def _organization_with_defaults(self, **kwargs):
        defaults = {
            'displayName': 'example_org_display'
        }
        defaults.update(kwargs)

        if 'hpoId' not in defaults:
            hpo = self.create_database_hpo()
            defaults['hpoId'] = hpo.hpoId

        return Organization(**defaults)

    def create_database_hpo(self, **kwargs):
        hpo = self._hpo_with_defaults(**kwargs)

        # hpoId is the primary key but is not automatically set when inserting
        if hpo.hpoId is None:
            hpo.hpoId = self.session.query(HPO).count() + 50  # There was code somewhere using lower numbers
        self._commit_to_database(hpo)

        return hpo

    def _hpo_with_defaults(self, **kwargs):
        return HPO(**kwargs)

    def create_database_participant(self, **kwargs):
        participant = self._participant_with_defaults(**kwargs)
        self._commit_to_database(participant)
        return participant

    def _participant_with_defaults(self, **kwargs):
        """Creates a new Participant model, filling in some default constructor args.

        This is intended especially for updates, where more fields are required than for inserts.
        """
        defaults = {
            'hpoId': UNSET_HPO_ID,
            'withdrawalStatus': WithdrawalStatus.NOT_WITHDRAWN,
            'suspensionStatus': SuspensionStatus.NOT_SUSPENDED,
            'participantOrigin': 'example',
            'version': 1,
            'lastModified': datetime.now(),
            'signUpTime': datetime.now()
        }
        defaults.update(kwargs)

        if 'biobankId' not in defaults:
            defaults['biobankId'] = self.unique_participant_biobank_id()
        if 'participantId' not in defaults:
            defaults['participantId'] = self.unique_participant_id()

        return Participant(**defaults)

    def create_database_participant_summary(self, **kwargs):
        participant_summary = self._participant_summary_with_defaults(**kwargs)
        self._commit_to_database(participant_summary)
        return participant_summary

    def _participant_summary_with_defaults(self, **kwargs):
        participant = kwargs.get('participant')
        if participant is None:
            participant = self.create_database_participant()

        defaults = {
            "participantId": participant.participantId,
            "biobankId": participant.biobankId,
            "hpoId": participant.hpoId,
            "firstName": self.faker.first_name(),
            "lastName": self.faker.last_name(),
            "numCompletedPPIModules": 0,
            "numCompletedBaselinePPIModules": 0,
            "numBaselineSamplesArrived": 0,
            "numberDistinctVisits": 0,
            "withdrawalStatus": WithdrawalStatus.NOT_WITHDRAWN,
            "suspensionStatus": SuspensionStatus.NOT_SUSPENDED,
            "enrollmentStatus": EnrollmentStatus.INTERESTED,
            "participantOrigin": participant.participantOrigin,
            "deceasedStatus": DeceasedStatus.UNSET
        }

        defaults.update(kwargs)
        for questionnaire_field in ['consentForStudyEnrollment']:
            if questionnaire_field in defaults:
                if f'{questionnaire_field}Time' not in defaults:
                    defaults[f'{questionnaire_field}Time'] = datetime.now()
                if f'{questionnaire_field}Authored' not in defaults:
                    defaults[f'{questionnaire_field}Authored'] = datetime.now()

        return ParticipantSummary(**defaults)

    @staticmethod
    def _participant_history_with_defaults(**kwargs):
        common_args = {
            "hpoId": UNSET_HPO_ID,
            "version": 1,
            "withdrawalStatus": WithdrawalStatus.NOT_WITHDRAWN,
            "suspensionStatus": SuspensionStatus.NOT_SUSPENDED,
            "participantOrigin": "example"
        }
        common_args.update(kwargs)
        return ParticipantHistory(**common_args)

    def create_database_code(self, **kwargs):
        code = self._code(**kwargs)
        self._commit_to_database(code)
        return code

    def _code(self, **kwargs):
        for field, default in [('system', PPI_SYSTEM),
                               ('codeType', 1),
                               ('mapped', False),
                               ('created', datetime.now())]:
            if field not in kwargs:
                kwargs[field] = default

        return Code(**kwargs)

    def create_database_biobank_order(self, **kwargs):
        biobank_order = self._biobank_order(**kwargs)
        self._commit_to_database(biobank_order)

        order_history = BiobankOrderHistory()
        order_history.fromdict(biobank_order.asdict(follow=["logPosition"]), allow_pk=True)
        self._commit_to_database(order_history)

        return biobank_order

    def _biobank_order(self, log_position=None, **kwargs):
        for field, default in [('version', 1),
                               ('created', datetime.now())]:
            if field not in kwargs:
                kwargs[field] = default

        if 'logPositionId' not in kwargs:
            if log_position is None:
                log_position = self.create_database_log_position()
            kwargs['logPositionId'] = log_position.logPositionId
        if 'biobankOrderId' not in kwargs:
            kwargs['biobankOrderId'] = self.unique_biobank_order_id()

        return BiobankOrder(**kwargs)

    def create_database_biobank_order_identifier(self, **kwargs):
        biobank_order_identifier = self._biobank_order_identifier(**kwargs)
        self._commit_to_database(biobank_order_identifier)
        return biobank_order_identifier

    def _biobank_order_identifier(self, **kwargs):
        return BiobankOrderIdentifier(**kwargs)

    def create_database_biobank_ordered_sample(self, **kwargs):
        biobank_ordered_sample = self._biobank_ordered_sample(**kwargs)
        self._commit_to_database(biobank_ordered_sample)

        ordered_sample_history = BiobankOrderedSampleHistory()
        ordered_sample_history.fromdict(biobank_ordered_sample.asdict(), allow_pk=True)
        ordered_sample_history.version = 1
        self._commit_to_database(ordered_sample_history)

        return biobank_ordered_sample

    def _biobank_ordered_sample(self, **kwargs):
        for field, default in [('description', 'test ordered sample'),
                               ('processingRequired', False),
                               ('test', 'C3PO')]:
            if field not in kwargs:
                kwargs[field] = default

        return BiobankOrderedSample(**kwargs)

    def create_database_biobank_stored_sample(self, **kwargs):
        biobank_stored_sample = self._biobank_stored_sample(**kwargs)
        self._commit_to_database(biobank_stored_sample)
        return biobank_stored_sample

    def _biobank_stored_sample(self, **kwargs):
        if 'biobankStoredSampleId' not in kwargs:
            kwargs['biobankStoredSampleId'] = self.unique_biobank_stored_sample_id()

        return BiobankStoredSample(**kwargs)

    def create_database_log_position(self, **kwargs):
        log_position = self._log_position(**kwargs)
        self._commit_to_database(log_position)
        return log_position

    def _log_position(self, **kwargs):
        return LogPosition(**kwargs)

    def create_database_api_user(self, **kwargs):
        api_user = self._api_user(**kwargs)
        self._commit_to_database(api_user)
        return api_user

    def _api_user(self, **kwargs):
        if 'system' not in kwargs:
            kwargs['system'] = 'unit_test'
        if 'username' not in kwargs:
            kwargs['username'] = 'me@test.com'
        return ApiUser(**kwargs)

    def create_database_deceased_report(self, **kwargs):
        deceased_report = self._deceased_report(**kwargs)
        self._commit_to_database(deceased_report)
        return deceased_report

    def _deceased_report(self, **kwargs):
        if 'participantId' not in kwargs:
            participant = self.create_database_participant()
            kwargs['participantId'] = participant.participantId
        if 'notification' not in kwargs:
            kwargs['notification'] = DeceasedNotification.EHR
        if 'author' not in kwargs:
            kwargs['author'] = self.create_database_api_user()
        if 'authored' not in kwargs:
            kwargs['authored'] = datetime.now()
        if 'status' not in kwargs:
            kwargs['status'] = DeceasedReportStatus.PENDING
        return DeceasedReport(**kwargs)
