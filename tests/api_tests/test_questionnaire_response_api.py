import datetime
import http.client
import json

import pytz
from dateutil.parser import parse
from sqlalchemy.orm.session import make_transient

from rdr_service.clock import FakeClock
from rdr_service.code_constants import PPI_EXTRA_SYSTEM, CONSENT_PERMISSION_YES_CODE, PPI_SYSTEM, \
    CONSENT_PERMISSION_NO_CODE
from rdr_service.dao.code_dao import CodeDao
from rdr_service.dao.participant_summary_dao import ParticipantGenderAnswersDao, ParticipantRaceAnswersDao
from rdr_service.dao.questionnaire_dao import QuestionnaireDao
from rdr_service.dao.questionnaire_response_dao import QuestionnaireResponseAnswerDao
from rdr_service.model.questionnaire_response import QuestionnaireResponseAnswer
from rdr_service.model.utils import from_client_participant_id
from rdr_service.participant_enums import QuestionnaireDefinitionStatus, ParticipantCohort, ParticipantCohortPilotFlag

from tests.test_data import data_path
from tests.helpers.unittest_base import BaseTestCase
from rdr_service.concepts import Concept

TIME_1 = datetime.datetime(2016, 1, 1)
TIME_2 = datetime.datetime(2016, 1, 2)
TIME_3 = datetime.datetime(2016, 1, 3)


def _questionnaire_response_url(participant_id):
    return "Participant/%s/QuestionnaireResponse" % participant_id


class QuestionnaireResponseApiTest(BaseTestCase):

    def setUp(self):
        super(QuestionnaireResponseApiTest, self).setUp()
        self._ehr_questionnaire_id = None
        self.participant_summary_default_values = {
            "ageRange": "UNSET",
            "race": "UNSET",
            "hpoId": "UNSET",
            "awardee": "UNSET",
            "site": "UNSET",
            "organization": "UNSET",
            "education": "UNSET",
            "income": "UNSET",
            "language": "UNSET",
            "primaryLanguage": "UNSET",
            "sex": "UNSET",
            "sexualOrientation": "UNSET",
            "state": "UNSET",
            "recontactMethod": "UNSET",
            "enrollmentStatus": "INTERESTED",
            "samplesToIsolateDNA": "UNSET",
            "numBaselineSamplesArrived": 0,
            "numCompletedPPIModules": 1,
            "numCompletedBaselinePPIModules": 1,
            "physicalMeasurementsStatus": "UNSET",
            "consentForGenomicsROR": "UNSET",
            "consentForDvElectronicHealthRecordsSharing": "UNSET",
            "consentForElectronicHealthRecords": "UNSET",
            "consentForStudyEnrollment": "SUBMITTED",
            "consentForCABoR": "UNSET",
            "questionnaireOnFamilyHealth": "UNSET",
            "questionnaireOnHealthcareAccess": "UNSET",
            "questionnaireOnMedicalHistory": "UNSET",
            "questionnaireOnMedications": "UNSET",
            "questionnaireOnOverallHealth": "UNSET",
            "questionnaireOnLifestyle": "UNSET",
            "questionnaireOnTheBasics": "SUBMITTED",
            "questionnaireOnCopeMay": "UNSET",
            "questionnaireOnCopeJune": "UNSET",
            "questionnaireOnCopeJuly": "UNSET",
            "questionnaireOnDnaProgram": "UNSET",
            "biospecimenCollectedSite": "UNSET",
            "biospecimenFinalizedSite": "UNSET",
            "biospecimenProcessedSite": "UNSET",
            "biospecimenSourceSite": "UNSET",
            "physicalMeasurementsCreatedSite": "UNSET",
            "physicalMeasurementsFinalizedSite": "UNSET",
            "biospecimenStatus": "UNSET",
            "sampleOrderStatus1ED04": "UNSET",
            "sampleOrderStatus1ED10": "UNSET",
            "sampleOrderStatus1HEP4": "UNSET",
            "sampleOrderStatus1PST8": "UNSET",
            "sampleOrderStatus1PS08": "UNSET",
            "sampleOrderStatus2PST8": "UNSET",
            "sampleOrderStatus1SAL": "UNSET",
            "sampleOrderStatus1SAL2": "UNSET",
            "sampleOrderStatus1SST8": "UNSET",
            "sampleOrderStatus2SST8": "UNSET",
            "sampleOrderStatus1SS08": "UNSET",
            "sampleOrderStatus1UR10": "UNSET",
            "sampleOrderStatus1UR90": "UNSET",
            "sampleOrderStatus2ED10": "UNSET",
            "sampleOrderStatus1CFD9": "UNSET",
            "sampleOrderStatus1PXR2": "UNSET",
            "sampleOrderStatus1ED02": "UNSET",
            "sampleOrderStatusDV1SAL2": "UNSET",
            "sampleStatus1ED04": "UNSET",
            "sampleStatus1ED10": "UNSET",
            "sampleStatus1HEP4": "UNSET",
            "sampleStatus1PST8": "UNSET",
            "sampleStatus2PST8": "UNSET",
            "sampleStatus1PS08": "UNSET",
            "sampleStatus1SAL": "UNSET",
            "sampleStatus1SAL2": "UNSET",
            "sampleStatus1SST8": "UNSET",
            "sampleStatus2SST8": "UNSET",
            "sampleStatus1SS08": "UNSET",
            "sampleStatus1UR10": "UNSET",
            "sampleStatus1UR90": "UNSET",
            "sampleStatus2ED10": "UNSET",
            "sampleStatus1CFD9": "UNSET",
            "sampleStatus1ED02": "UNSET",
            "sampleStatus1PXR2": "UNSET",
            "sampleStatusDV1SAL2": "UNSET",
            "withdrawalStatus": "NOT_WITHDRAWN",
            "withdrawalReason": "UNSET",
            "suspensionStatus": "NOT_SUSPENDED",
            "numberDistinctVisits": 0,
            "ehrStatus": "UNSET",
            "ehrConsentExpireStatus": "UNSET",
            "patientStatus": [],
            "participantOrigin": 'example',
            "semanticVersionForPrimaryConsent": "v1",
            "deceasedStatus": "UNSET",
            "retentionEligibleStatus": "NOT_ELIGIBLE"
        }

    def test_duplicate_consent_submission(self):
        """
    Submit duplicate study enrollment questionnaires, so we can make sure
    a duplicate submission doesn't error out and the authored timestamp will
    not be updated if the answer is not changed.
    """
        participant_id = self.create_participant()
        authored_1 = datetime.datetime(2019, 3, 16, 1, 39, 33, tzinfo=pytz.utc)
        created = datetime.datetime(2019, 3, 16, 1, 51, 22)
        with FakeClock(created):
            self.send_consent(participant_id, authored=authored_1)

        summary = self.send_get("Participant/{0}/Summary".format(participant_id))
        self.assertEqual(parse(summary["consentForStudyEnrollmentTime"]), created.replace(tzinfo=None))
        self.assertEqual(parse(summary["consentForStudyEnrollmentAuthored"]), authored_1.replace(tzinfo=None))

        # submit consent questionnaire again with new timestamps.
        authored_2 = datetime.datetime(2019, 3, 17, 1, 24, 16, tzinfo=pytz.utc)
        with FakeClock(datetime.datetime(2019, 3, 17, 1, 25, 58)):
            self.send_consent(participant_id, authored=authored_2)

        summary = self.send_get("Participant/{0}/Summary".format(participant_id))
        # created should remain the same as the first submission.
        self.assertEqual(parse(summary["consentForStudyEnrollmentTime"]), created.replace(tzinfo=None))
        self.assertEqual(parse(summary["consentForStudyEnrollmentAuthored"]), authored_1.replace(tzinfo=None))

    def test_ehr_consent_expired(self):
        participant_id = self.create_participant()
        authored_1 = datetime.datetime(2019, 3, 16, 1, 39, 33, tzinfo=pytz.utc)
        created = datetime.datetime(2019, 3, 16, 1, 51, 22)
        with FakeClock(created):
            self.send_consent(participant_id, authored=authored_1)
        summary = self.send_get("Participant/{0}/Summary".format(participant_id))
        self.assertEqual(parse(summary["consentForStudyEnrollmentTime"]), created.replace(tzinfo=None))
        self.assertEqual(parse(summary["consentForStudyEnrollmentAuthored"]), authored_1.replace(tzinfo=None))

        self.assertEqual(summary.get('consentForElectronicHealthRecordsAuthored'), None)
        self.assertEqual(summary.get('enrollmentStatusMemberTime'), None)
        self.assertEqual(summary.get('enrollmentStatus'), 'INTERESTED')

        self._ehr_questionnaire_id = self.create_questionnaire("ehr_consent_questionnaire.json")

        # send ConsentPermission_Yes questionnaire response
        with FakeClock(datetime.datetime(2020, 3, 12)):
            self.submit_ehr_questionnaire(participant_id, CONSENT_PERMISSION_YES_CODE, None,
                                          datetime.datetime(2020, 2, 12))
        summary = self.send_get("Participant/{0}/Summary".format(participant_id))
        self.assertEqual(summary.get('consentForElectronicHealthRecordsAuthored'), '2020-02-12T00:00:00')
        self.assertEqual(summary.get('enrollmentStatusMemberTime'), '2020-03-12T00:00:00')
        self.assertEqual(summary.get('enrollmentStatus'), 'MEMBER')
        self.assertEqual(summary.get('ehrConsentExpireStatus'), 'UNSET')

        summary2 = self.send_get("ParticipantSummary?_count=25&_offset=0&_sort%3Adesc=consentForStudyEnrollmentAuthored"
                                 "&consentForElectronicHealthRecords=SUBMITTED&ehrConsentExpireStatus=UNSET"
                                 "&_includeTotal=true")
        self.assertEqual(len(summary2.get('entry')), 1)

        # send EHRConsentPII_ConsentExpired_Yes questionnaire response
        # response payload sample
        # {
        #     "resourceType": "QuestionnaireResponse",
        #     "extension": [
        #         {
        #             "url": "http://hl7.org/fhir/StructureDefinition/iso21090-ST-language",
        #             "valueCode": "en"
        #         }
        #     ],
        #     "identifier": {
        #         "value": "1592553285370"
        #     },
        #     "questionnaire": {
        #         "reference": "Questionnaire/475180/_history/V2020.04.20"
        #     },
        #     "status": "completed",
        #     "subject": {
        #         "reference": "Patient/P443846736"
        #     },
        #     "authored": "2020-06-19T07:54:45+00:00",
        #     "group": {
        #         "linkId": "root_group",
        #         "title": "Consent to Share Electronic Health Records",
        #         "text": "Consent to Share Electronic Health Records",
        #         "question": [
        #             {
        #                 "linkId": "7068",
        #                 "text": "EHRConsentPII_ConsentPermission",
        #                 "answer": [
        #                     {
        #                         "valueCoding": {
        #                             "system": "http://terminology.pmi-ops.org/CodeSystem/ppi",
        #                             "code": "ConsentPermission_No",
        #                             "display": "No, I do not wish to give All of Us access to my EHR"
        #                         }
        #                     }
        #                 ]
        #             },
        #             {
        #                 "linkId": "47771",
        #                 "text": "EHRConsentPII_ConsentExpired",
        #                 "answer": [
        #                     {
        #                         "valueString": "EHRConsentPII_ConsentExpired_Yes"
        #                     }
        #                 ]
        #             }
        #         ]
        #     },
        #     "id": "431459662"
        # }
        with FakeClock(datetime.datetime(2020, 4, 12)):
            string_answer = ['ehrConsentExpired', 'EHRConsentPII_ConsentExpired_Yes']
            self.submit_ehr_questionnaire(participant_id, CONSENT_PERMISSION_NO_CODE, [string_answer],
                                          datetime.datetime(2020, 3, 20))
        summary = self.send_get("Participant/{0}/Summary".format(participant_id))
        self.assertEqual(summary.get('consentForElectronicHealthRecordsAuthored'), '2020-03-20T00:00:00')
        self.assertEqual(summary.get('consentForElectronicHealthRecords'), 'SUBMITTED_NO_CONSENT')
        # keep the same behaviour with the withdrawal participant for enrollmentStatusMemberTime
        self.assertEqual(summary.get('enrollmentStatusMemberTime'), None)
        self.assertEqual(summary.get('enrollmentStatus'), 'INTERESTED')
        self.assertEqual(summary.get('ehrConsentExpireStatus'), 'EXPIRED')
        self.assertEqual(summary.get('ehrConsentExpireTime'), '2020-04-12T00:00:00')
        self.assertEqual(summary.get('ehrConsentExpireAuthored'), '2020-03-20T00:00:00')

        # test participant summary api ehr consent expire status returns right info
        summary2 = self.send_get("ParticipantSummary?_count=25&_offset=0&_sort%3Adesc=consentForStudyEnrollmentAuthored"
                                 "&consentForElectronicHealthRecords=SUBMITTED_NO_CONSENT"
                                 "&ehrConsentExpireStatus=EXPIRED&_includeTotal=true")
        self.assertEqual(len(summary2.get('entry')), 1)

        # test re-sign ehr consent
        with FakeClock(datetime.datetime(2020, 4, 12)):
            self.submit_ehr_questionnaire(participant_id, CONSENT_PERMISSION_YES_CODE, None,
                                          datetime.datetime(2020, 4, 11))
        summary = self.send_get("Participant/{0}/Summary".format(participant_id))
        self.assertEqual(summary.get('consentForElectronicHealthRecordsAuthored'), '2020-04-11T00:00:00')
        self.assertEqual(summary.get('enrollmentStatusMemberTime'), '2020-04-12T00:00:00')
        self.assertEqual(summary.get('enrollmentStatus'), 'MEMBER')
        self.assertEqual(summary.get('ehrConsentExpireStatus'), 'UNSET')
        self.assertEqual(summary.get('ehrConsentExpireTime'), None)
        self.assertEqual(summary.get('ehrConsentExpireAuthored'), None)

        summary2 = self.send_get("ParticipantSummary?_count=25&_offset=0&_sort%3Adesc=consentForStudyEnrollmentAuthored"
                                 "&consentForElectronicHealthRecords=SUBMITTED&ehrConsentExpireStatus=UNSET"
                                 "&_includeTotal=true")
        self.assertEqual(len(summary2.get('entry')), 1)

    def submit_ehr_questionnaire(self, participant_id, ehr_response_code, string_answers, authored):
        if not self._ehr_questionnaire_id:
            self._ehr_questionnaire_id = self.create_questionnaire("ehr_consent_questionnaire.json")
        code_answers = []
        if ehr_response_code:
            _add_code_answer(code_answers, 'ehrConsent', ehr_response_code)
        qr_json = self.make_questionnaire_response_json(
            participant_id,
            self._ehr_questionnaire_id,
            string_answers=string_answers,
            code_answers=code_answers,
            authored=authored
        )
        self.send_post(self.questionnaire_response_url(participant_id), qr_json)

    def test_insert_raises_400_for_excessively_long_valueString(self):
        participant_id = self.create_participant()
        questionnaire_id = self.create_questionnaire("questionnaire1.json")
        url = _questionnaire_response_url(participant_id)

        # Remember we need to send the consent first
        self.send_consent(participant_id)

        # Check that a string of exactly the max length will post
        # This one should be exactly long enough to pass
        string = "a" * QuestionnaireResponseAnswer.VALUE_STRING_MAXLEN
        string_answers = [["nameOfChild", string]]
        resource = self.make_questionnaire_response_json(participant_id, questionnaire_id, string_answers=string_answers)
        response = self.send_post(url, resource)
        self.assertEqual(response["group"]["question"][0]["answer"][0]["valueString"], string)

        # Check that a string longer than the max will not
        # This one should evaluate to a string that is one char too long; i.e. exactly 64KiB
        string = "a" * (QuestionnaireResponseAnswer.VALUE_STRING_MAXLEN + 1)
        string_answers = [["nameOfChild", string]]
        resource = self.make_questionnaire_response_json(participant_id, questionnaire_id, string_answers=string_answers)
        self.send_post(url, resource, expected_status=http.client.BAD_REQUEST)

    def test_insert(self):
        participant_id = self.create_participant()
        questionnaire_id = self.create_questionnaire("questionnaire1.json")
        with open(data_path("questionnaire_response3.json")) as fd:
            resource = json.load(fd)

        # Sending response with the dummy participant id in the file is an error
        self.send_post(
            _questionnaire_response_url("{participant_id}"), resource, expected_status=http.client.NOT_FOUND
        )

        # Fixing participant id but not the questionnaire id is also an error
        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        self.send_post(_questionnaire_response_url(participant_id), resource, expected_status=http.client.BAD_REQUEST)

        # Fix the reference
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        # Sending the response before the consent is an error.
        self.send_post(_questionnaire_response_url(participant_id), resource, expected_status=http.client.BAD_REQUEST)

        # After consent, the post succeeds
        self.send_consent(participant_id)
        response = self.send_post(_questionnaire_response_url(participant_id), resource)
        resource["id"] = response["id"]
        # The resource gets rewritten to include the version
        resource['questionnaire']['reference'] = 'Questionnaire/%s/_history/aaa' % questionnaire_id
        self.assertJsonResponseMatches(resource, response)

        #  sending an update response with history reference
        with open(data_path('questionnaire_response4.json')) as fd:
            update_resource = json.load(fd)
        update_resource['subject']['reference'] = \
            update_resource['subject']['reference'].format(participant_id=participant_id)
        update_resource['questionnaire']['reference'] = \
            update_resource['questionnaire']['reference'].format(questionnaire_id=questionnaire_id,
                                                                 semantic_version='aaa')
        response = self.send_post(_questionnaire_response_url(participant_id), update_resource)
        update_resource['id'] = response['id']
        self.assertJsonResponseMatches(update_resource, response)

        # Do a get to fetch the questionnaire
        get_response = self.send_get(_questionnaire_response_url(participant_id) + "/" + response["id"])
        self.assertJsonResponseMatches(update_resource, get_response)

        code_dao = CodeDao()

        # Ensure we didn't create codes in the extra system
        self.assertIsNone(code_dao.get_code(PPI_EXTRA_SYSTEM, "IgnoreThis"))

        name_of_child = code_dao.get_code("sys", "nameOfChild")
        birth_weight = code_dao.get_code("sys", "birthWeight")
        birth_length = code_dao.get_code("sys", "birthLength")
        vitamin_k_dose_1 = code_dao.get_code("sys", "vitaminKDose1")
        vitamin_k_dose_2 = code_dao.get_code("sys", "vitaminKDose2")
        hep_b_given = code_dao.get_code("sys", "hepBgiven")
        abnormalities_at_birth = code_dao.get_code("sys", "abnormalitiesAtBirth")
        answer_dao = QuestionnaireResponseAnswerDao()
        with answer_dao.session() as session:
            code_ids = [
                code.codeId
                for code in [
                    name_of_child,
                    birth_weight,
                    birth_length,
                    vitamin_k_dose_1,
                    vitamin_k_dose_2,
                    hep_b_given,
                    abnormalities_at_birth,
                ]
            ]
            current_answers = answer_dao.get_current_answers_for_concepts(
                session, from_client_participant_id(participant_id), code_ids
            )
        self.assertEqual(7, len(current_answers))
        questionnaire = QuestionnaireDao().get_with_children(questionnaire_id)
        question_id_to_answer = {answer.questionId: answer for answer in current_answers}
        code_id_to_answer = {
            question.codeId: question_id_to_answer.get(question.questionnaireQuestionId)
            for question in questionnaire.questions
        }
        self.assertEqual("Cathy Jones", code_id_to_answer[name_of_child.codeId].valueString)
        self.assertEqual(3.25, code_id_to_answer[birth_weight.codeId].valueDecimal)
        self.assertEqual(44.3, code_id_to_answer[birth_length.codeId].valueDecimal)
        self.assertEqual(44, code_id_to_answer[birth_length.codeId].valueInteger)
        self.assertEqual(True, code_id_to_answer[hep_b_given.codeId].valueBoolean)
        self.assertEqual(0, code_id_to_answer[abnormalities_at_birth.codeId].valueInteger)
        self.assertEqual(datetime.date(1972, 11, 30), code_id_to_answer[vitamin_k_dose_1.codeId].valueDate)
        self.assertEqual(
            datetime.datetime(1972, 11, 30, 12, 34, 42), code_id_to_answer[vitamin_k_dose_2.codeId].valueDateTime
        )

    def test_demographic_questionnaire_responses(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)
        expected = self.participant_summary_default_values
        expected.update({
            "genderIdentity": "GenderIdentity_NonBinary",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "questionnaireOnTheBasicsTime": TIME_2.isoformat(),
            "questionnaireOnTheBasicsAuthored": TIME_2.isoformat(),
            "signUpTime": TIME_1.isoformat(),
            "consentCohort": str(ParticipantCohort.COHORT_1),
            "cohort2PilotFlag": str(ParticipantCohortPilotFlag.UNSET)
        })
        self.assertJsonResponseMatches(expected, summary)

    def test_gror_consent(self):
        """WIP: The json files associated with this test may need to change.
        Requirements are still being worked out on PTSC side and this was made
        before finalization."""
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id, language="es")

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)

        expected = self.participant_summary_default_values
        expected.update({
            "genderIdentity": "UNSET",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "numCompletedPPIModules": 0,
            "numCompletedBaselinePPIModules": 0,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "primaryLanguage": "es",
            "questionnaireOnTheBasics": "UNSET",
            "signUpTime": TIME_1.isoformat(),
            "consentCohort": str(ParticipantCohort.COHORT_1),
            "cohort2PilotFlag": str(ParticipantCohortPilotFlag.UNSET)
        })
        self.assertJsonResponseMatches(expected, summary)

        # verify if the response is not consent, the primary language will not change
        questionnaire_id = self.create_questionnaire("consent_for_genomic_ror_question.json")

        with open(data_path("consent_for_genomic_ror_resp.json")) as f:
            resource = json.load(f)
            resource["subject"]["reference"] = f'Patient/{participant_id}'
            resource["questionnaire"]["reference"] = f'Questionnaire/{questionnaire_id}'

            self.send_post(_questionnaire_response_url(participant_id), resource)

            summary = self.send_get("Participant/%s/Summary" % participant_id)
            self.assertEqual(summary['consentForGenomicsROR'], 'SUBMITTED')

        with open(data_path("consent_for_genomic_ror_dont_know.json")) as f:
            dont_know_resp = json.load(f)

        dont_know_resp["subject"]["reference"] = f'Patient/{participant_id}'
        dont_know_resp["questionnaire"]["reference"] = f'Questionnaire/{questionnaire_id}'

        with FakeClock(TIME_2):
            self.send_post(_questionnaire_response_url(participant_id), dont_know_resp)

        summary = self.send_get("Participant/%s/Summary" % participant_id)
        self.assertEqual(summary['semanticVersionForPrimaryConsent'], 'v1')
        self.assertEqual(summary['consentForGenomicsRORTime'], TIME_2.isoformat())
        self.assertEqual(summary['consentForGenomicsRORAuthored'], '2019-12-12T09:30:44')
        self.assertEqual(summary['consentForGenomicsROR'], 'SUBMITTED_NOT_SURE')

        with open(data_path("consent_for_genomic_ror_no.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = f'Patient/{participant_id}'
        resource["questionnaire"]["reference"] = f'Questionnaire/{questionnaire_id}'

        with FakeClock(TIME_2):
            self.send_post(_questionnaire_response_url(participant_id), resource)

        summary = self.send_get("Participant/%s/Summary" % participant_id)
        self.assertEqual(summary['semanticVersionForPrimaryConsent'], 'v1')
        self.assertEqual(summary['consentForGenomicsROR'], 'SUBMITTED_NO_CONSENT')
        self.assertEqual(summary['consentForGenomicsRORTime'], TIME_2.isoformat())
        self.assertEqual(summary['consentForGenomicsRORAuthored'], '2019-12-12T09:30:44')

        # Test Bad Code Value Sent returns 400
        with open(data_path("consent_for_genomic_ror_bad_request.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = f'Patient/{participant_id}'
        resource["questionnaire"]["reference"] = f'Questionnaire/{questionnaire_id}'

        with FakeClock(TIME_2):
            self.send_post(_questionnaire_response_url(participant_id),
                           resource,
                           expected_status=http.client.BAD_REQUEST)

    def test_consent_with_extension_language(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id, language="es")

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)

        expected = self.participant_summary_default_values
        expected.update({
            "genderIdentity": "UNSET",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "numCompletedPPIModules": 0,
            "numCompletedBaselinePPIModules": 0,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "primaryLanguage": "es",
            "questionnaireOnTheBasics": "UNSET",
            "signUpTime": TIME_1.isoformat(),
            "consentCohort": str(ParticipantCohort.COHORT_1),
            "cohort2PilotFlag": str(ParticipantCohortPilotFlag.UNSET)
        })
        self.assertJsonResponseMatches(expected, summary)

        # verify if the response is not consent, the primary language will not change
        questionnaire_id = self.create_questionnaire("questionnaire_family_history.json")

        with open(data_path("questionnaire_family_history_resp.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )
        with FakeClock(TIME_2):
            self.send_post(_questionnaire_response_url(participant_id), resource)

        summary = self.send_get("Participant/%s/Summary" % participant_id)

        self.assertEqual(expected["primaryLanguage"], summary["primaryLanguage"])

    def test_invalid_questionnaire(self):
        participant_id = self.create_participant()
        questionnaire_id = self.create_questionnaire("questionnaire1.json")
        q = QuestionnaireDao()
        quesstionnaire = q.get(questionnaire_id)
        make_transient(quesstionnaire)
        quesstionnaire.status = QuestionnaireDefinitionStatus.INVALID
        with q.session() as session:
            existing_obj = q.get_for_update(session, q.get_id(quesstionnaire))
            q._do_update(session, quesstionnaire, existing_obj)
        q.get(questionnaire_id)

        with open(data_path("questionnaire_response3.json")) as fd:
            resource = json.load(fd)

        self.send_consent(participant_id)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        # The resource gets rewritten to include the version
        resource["questionnaire"]["reference"] = "Questionnaire/%s" % questionnaire_id
        self.send_post(_questionnaire_response_url(participant_id), resource, expected_status=http.client.BAD_REQUEST)
        resource["questionnaire"]["reference"] = "Questionnaire/%s/_history/2" % questionnaire_id
        self.send_post(_questionnaire_response_url(participant_id), resource, expected_status=http.client.BAD_REQUEST)

    def test_response_allows_for_missing_group(self):
        participant_id = self.create_participant()
        self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire1.json")

        with open(data_path("questionnaire_response_empty.json")) as fd:
            resource = json.load(fd)
        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = "Questionnaire/%s" % questionnaire_id
        self.send_post(_questionnaire_response_url(participant_id), resource)  # will fail if status 200 isn't returned

    def test_invalid_questionnaire_linkid(self):
        """
    DA-623 - Make sure that an invalid link id in response triggers a BadRequest status.
    Per a PTSC group request, only log a message for invalid link ids.
    In the future if questionnaires with bad link ids trigger a BadRequest, the code below
    can be uncommented.
    """
        participant_id = self.create_participant()
        self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_family_history.json")

        with open(data_path("questionnaire_family_history_resp.json")) as fd:
            resource = json.load(fd)

        # update resource json to set participant and questionnaire ids.
        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        self.send_post(_questionnaire_response_url(participant_id), resource, expected_status=http.client.OK)

        # Alter response to set a bad link id value
        # resource['group']['question'][0]['linkId'] = 'bad-link-id'

        # # DA-623 - Per the PTSC groups request, invalid link ids only log a message for
        # invalid link ids.
        # self.send_post(_questionnaire_response_url(participant_id), resource,
        #                           expected_status=httplib.BAD_REQUEST)

    def test_multiple_genders(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp_multiple_gender.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)
        expected = {
            "genderIdentity": "GenderIdentity_MoreThanOne",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "questionnaireOnTheBasicsTime": TIME_2.isoformat(),
            "questionnaireOnTheBasicsAuthored": TIME_2.isoformat(),
            "signUpTime": TIME_1.isoformat(),
            "consentCohort": str(ParticipantCohort.COHORT_1),
            "cohort2PilotFlag": str(ParticipantCohortPilotFlag.UNSET)
        }
        expected.update(self.participant_summary_default_values)
        self.assertJsonResponseMatches(expected, summary)

    def test_participant_gender_answers(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp_multiple_gender.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        participant_gender_answers_dao = ParticipantGenderAnswersDao()
        answers = participant_gender_answers_dao.get_all()
        self.assertEqual(len(answers), 2)
        for answer in answers:
            self.assertIn(answer.codeId, [91, 92])

        # resubmit the answers, old value should be removed
        with open(data_path("questionnaire_the_basics_resp_multiple_gender_2.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        answers = participant_gender_answers_dao.get_all()
        self.assertEqual(len(answers), 2)
        for answer in answers:
            self.assertIn(answer.codeId, [91, 100])

    def test_participant_race_answers(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp_multiple_race.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        code_dao = CodeDao()
        code1 = code_dao.get_code("http://terminology.pmi-ops.org/CodeSystem/ppi", "WhatRaceEthnicity_White")
        code2 = code_dao.get_code("http://terminology.pmi-ops.org/CodeSystem/ppi", "WhatRaceEthnicity_Hispanic")

        participant_race_answers_dao = ParticipantRaceAnswersDao()
        answers = participant_race_answers_dao.get_all()
        self.assertEqual(len(answers), 2)
        for answer in answers:
            self.assertIn(answer.codeId, [code1.codeId, code2.codeId])

        # resubmit the answers, old value should be removed
        with open(data_path("questionnaire_the_basics_resp_multiple_race_2.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        code_dao = CodeDao()
        code1 = code_dao.get_code("http://terminology.pmi-ops.org/CodeSystem/ppi", "WhatRaceEthnicity_NHPI")
        code2 = code_dao.get_code("http://terminology.pmi-ops.org/CodeSystem/ppi", "PMI_PreferNotToAnswer")

        answers = participant_race_answers_dao.get_all()
        self.assertEqual(len(answers), 2)
        for answer in answers:
            self.assertIn(answer.codeId, [code1.codeId, code2.codeId])

    def test_gender_plus_skip_equals_gender(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp_multiple_gender.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )
        resource["group"]["question"][2]["answer"][1]["valueCoding"]["code"] = "PMI_Skip"

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)
        expected = {
            "genderIdentity": "GenderIdentity_Man",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "questionnaireOnTheBasicsTime": TIME_2.isoformat(),
            "questionnaireOnTheBasicsAuthored": TIME_2.isoformat(),
            "signUpTime": TIME_1.isoformat(),
        }
        expected.update(self.participant_summary_default_values)
        self.assertJsonResponseMatches(expected, summary)

    def test_gender_prefer_not_answer(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp.json")) as f:
            resource = json.load(f)

        resource["group"]["question"][2]["answer"][0]["valueCoding"]["code"] = "PMI_PreferNotToAnswer"
        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)
        expected = {
            "genderIdentity": "PMI_PreferNotToAnswer",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "questionnaireOnTheBasicsTime": TIME_2.isoformat(),
            "questionnaireOnTheBasicsAuthored": TIME_2.isoformat(),
            "signUpTime": TIME_1.isoformat(),
            "consentCohort": str(ParticipantCohort.COHORT_1),
            "cohort2PilotFlag": str(ParticipantCohortPilotFlag.UNSET)
        }
        expected.update(self.participant_summary_default_values)
        self.assertJsonResponseMatches(expected, summary)

    def test_gender_plus_skip_equals_gender(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp_multiple_gender.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )
        resource["group"]["question"][2]["answer"][1]["valueCoding"]["code"] = "PMI_Skip"

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        participant = self.send_get("Participant/%s" % participant_id)
        summary = self.send_get("Participant/%s/Summary" % participant_id)
        expected = {
            "genderIdentity": "GenderIdentity_Man",
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "streetAddress": self.streetAddress,
            "streetAddress2": self.streetAddress2,
            "biobankId": participant["biobankId"],
            "participantId": participant_id,
            "consentForStudyEnrollmentTime": TIME_1.isoformat(),
            "consentForStudyEnrollmentAuthored": TIME_1.isoformat(),
            "consentForStudyEnrollmentFirstYesAuthored": TIME_1.isoformat(),
            "questionnaireOnTheBasicsTime": TIME_2.isoformat(),
            "questionnaireOnTheBasicsAuthored": TIME_2.isoformat(),
            "signUpTime": TIME_1.isoformat(),
            "consentCohort": str(ParticipantCohort.COHORT_1),
            "cohort2PilotFlag": str(ParticipantCohortPilotFlag.UNSET)
        }
        expected.update(self.participant_summary_default_values)
        self.assertJsonResponseMatches(expected, summary)

    def test_different_origin_cannot_submit(self):
        with FakeClock(TIME_1):
            participant_id = self.create_participant()
            self.send_consent(participant_id)

        questionnaire_id = self.create_questionnaire("questionnaire_the_basics.json")

        with open(data_path("questionnaire_the_basics_resp.json")) as f:
            resource = json.load(f)

        resource["subject"]["reference"] = resource["subject"]["reference"].format(participant_id=participant_id)
        resource["questionnaire"]["reference"] = resource["questionnaire"]["reference"].format(
            questionnaire_id=questionnaire_id
        )

        with FakeClock(TIME_2):
            resource["authored"] = TIME_2.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource)

        summary = self.send_get("Participant/%s/Summary" % participant_id)
        self.assertEqual(summary["participantOrigin"], "example")

        with FakeClock(TIME_3):
            BaseTestCase.switch_auth_user("example@sabrina.com", "vibrent")
            resource["authored"] = TIME_3.isoformat()
            self.send_post(_questionnaire_response_url(participant_id), resource, expected_status=http.client.BAD_REQUEST)

            BaseTestCase.switch_auth_user("example@example.com", "example")
            summary = self.send_get("Participant/%s/Summary" % participant_id)
            # Posting a QR should not change origin.
            self.assertEqual(summary["participantOrigin"], "example")


def _add_code_answer(code_answers, link_id, code):
    if code:
        code_answers.append((link_id, Concept(PPI_SYSTEM, code)))
