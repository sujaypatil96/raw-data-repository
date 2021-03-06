import http.client
import json

from rdr_service.code_constants import PPI_EXTRA_SYSTEM
from rdr_service.dao.code_dao import CodeDao
from tests.test_data import data_path
from tests.helpers.unittest_base import BaseTestCase


class QuestionnaireApiTest(BaseTestCase):
    def test_insert(self):
        questionnaire_files = ("questionnaire1.json", "questionnaire2.json", "questionnaire_demographics.json")

        for json_file in questionnaire_files:
            with open(data_path(json_file)) as f:
                questionnaire = json.load(f)
            response = self.send_post("Questionnaire", questionnaire)
            questionnaire_id = response["id"]
            del response["id"]
            self.assertJsonResponseMatches(questionnaire, response)

            response = self.send_get("Questionnaire/%s" % questionnaire_id)
            del response["id"]
            self.assertJsonResponseMatches(questionnaire, response)

        # Ensure we didn't create codes in the extra system
        self.assertIsNone(CodeDao().get_code(PPI_EXTRA_SYSTEM, "IgnoreThis"))

    def insert_questionnaire(self):
        with open(data_path("questionnaire1.json")) as f:
            questionnaire = json.load(f)
            return self.send_post("Questionnaire", questionnaire, expected_response_headers={'ETag': 'W/"aaa"'})

    def test_update_before_insert(self):
        with open(data_path("questionnaire1.json")) as f:
            questionnaire = json.load(f)
            self.send_put("Questionnaire/1", questionnaire, expected_status=http.client.BAD_REQUEST)

    def test_update_no_ifmatch_specified(self):
        response = self.insert_questionnaire()

        with open(data_path("questionnaire2.json")) as f2:
            questionnaire2 = json.load(f2)
            self.send_put("Questionnaire/%s" % response["id"], questionnaire2, expected_status=http.client.BAD_REQUEST)

    def test_update_invalid_ifmatch_specified(self):
        response = self.insert_questionnaire()

        with open(data_path("questionnaire2.json")) as f2:
            questionnaire2 = json.load(f2)
            self.send_put(
                "Questionnaire/%s" % response["id"],
                questionnaire2,
                expected_status=http.client.BAD_REQUEST,
                headers={"If-Match": "Blah"},
            )

    def test_update_wrong_ifmatch_specified(self):
        response = self.insert_questionnaire()

        with open(data_path("questionnaire2.json")) as f2:
            questionnaire2 = json.load(f2)
            self.send_put(
                "Questionnaire/%s" % response["id"],
                questionnaire2,
                expected_status=http.client.PRECONDITION_FAILED,
                headers={"If-Match": 'W/"123"'},
            )

    def test_update_right_ifmatch_specified(self):
        response = self.insert_questionnaire()
        self.assertEqual('W/"aaa"', response['meta']['versionId'])
        with open(data_path("questionnaire2.json")) as f2:
            questionnaire2 = json.load(f2)
            update_response = self.send_put(
                "Questionnaire/%s" % response["id"],
                questionnaire2,
                headers={'If-Match': response['meta']['versionId']},
                expected_response_headers={'ETag': 'W/"bbb"'}
            )
        questionnaire2["id"] = response["id"]
        self.assertJsonResponseMatches(questionnaire2, update_response)
        self.assertEqual('W/"bbb"', update_response['meta']['versionId'])

    def test_update_with_duplicate_semantic_version(self):
        response = self.insert_questionnaire()
        self.assertEqual('W/"aaa"', response['meta']['versionId'])
        with open(data_path("questionnaire2.json")) as f2:
            questionnaire2 = json.load(f2)
            questionnaire2['version'] = 'aaa'
            self.send_put(
                "Questionnaire/%s" % response["id"],
                questionnaire2,
                headers={'If-Match': response['meta']['versionId']},
                expected_status=http.client.BAD_REQUEST
            )

    def test_insert_with_version(self):
        with open(data_path('questionnaire5_with_version.json')) as f:
            questionnaire = json.load(f)
        response = self.send_post('Questionnaire', questionnaire)
        questionnaire_id = response['id']
        del response['id']
        questionnaire['version'] = 'abc123'
        self.assertJsonResponseMatches(questionnaire, response)

        response = self.send_get('Questionnaire/%s' % questionnaire_id)
        del response['id']
        self.assertJsonResponseMatches(questionnaire, response)

        # Ensure we didn't create codes in the extra system
        self.assertIsNone(CodeDao().get_code(PPI_EXTRA_SYSTEM, 'IgnoreThis'))

