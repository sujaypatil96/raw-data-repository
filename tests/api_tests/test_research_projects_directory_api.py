from tests.helpers.unittest_base import BaseTestCase


class ResearchProjectsDirectoryApiTest(BaseTestCase):
    def setUp(self):
        super().setUp(with_data=False)

    def test_get_research_projects_directory(self):
        # create researchers
        researchers_json = [
            {
                "userId": 0,
                "creationTime": "2019-11-26T21:21:13.056Z",
                "modifiedTime": "2019-11-26T21:21:13.056Z",
                "givenName": "given name 1",
                "familyName": "family name 1",
                "streetAddress1": "string",
                "streetAddress2": "string",
                "city": "string",
                "state": "string",
                "zipCode": "string",
                "country": "string",
                "ethnicity": "HISPANIC",
                "gender": ["MALE"],
                "race": ["AIAN"],
                "sexAtBirth": "FEMALE",
                "sexualOrientation": "BISEXUAL",
                "affiliations": [
                    {
                        "institution": "institution1",
                        "role": "institution role 1",
                        "nonAcademicAffiliation": "INDUSTRY"
                    }
                ]
            },
            {
                "userId": 1,
                "creationTime": "2019-11-27T21:21:13.056Z",
                "modifiedTime": "2019-11-27T21:21:13.056Z",
                "givenName": "given name 2",
                "familyName": "family name 2",
                "streetAddress1": "string2",
                "streetAddress2": "string2",
                "city": "string2",
                "state": "string2",
                "zipCode": "string2",
                "country": "string2",
                "ethnicity": "HISPANIC",
                "sexAtBirth": "FEMALE",
                "sexualOrientation": "BISEXUAL",
                "gender": ["MALE", "FEMALE"],
                "race": ["AIAN", "WHITE"],
                "affiliations": [
                    {
                        "institution": "institution2",
                        "role": "institution role 2"
                    },
                    {
                        "institution": "institution22",
                        "role": "institution role 22",
                        "nonAcademicAffiliation": "INDUSTRY"
                    }
                ]
            }
        ]
        self.send_post('workbench/directory/researchers', request_data=researchers_json)

        # create workspace
        request_json = [
            {
                "workspaceId": 0,
                "name": "workspace name str",
                "creationTime": "2019-11-25T17:43:41.085Z",
                "modifiedTime": "2019-11-25T17:43:41.085Z",
                "status": "ACTIVE",
                "workspaceUsers": [
                    {
                        "userId": 0,
                        "role": "READER",
                        "status": "ACTIVE"
                    },
                    {
                        "userId": 1,
                        "role": "OWNER",
                        "status": "ACTIVE"
                    }
                ],
                "excludeFromPublicDirectory": True,
                "diseaseFocusedResearch": True,
                "diseaseFocusedResearchName": "disease focused research name str",
                "otherPurposeDetails": "other purpose details str",
                "methodsDevelopment": True,
                "controlSet": True,
                "ancestry": True,
                "socialBehavioral": True,
                "populationHealth": True,
                "drugDevelopment": True,
                "commercialPurpose": True,
                "educational": True,
                "otherPurpose": True,
                "reasonForInvestigation": 'reasonForInvestigation string',
                "intendToStudy": 'intendToStudy string',
                "findingsFromStudy": 'findingsFromStudy string'
            },
            {
                "workspaceId": 1,
                "name": "workspace name str 2",
                "creationTime": "2019-11-25T17:43:41.085Z",
                "modifiedTime": "2019-11-25T17:43:41.085Z",
                "status": "INACTIVE",
                "workspaceUsers": [
                    {
                        "userId": 0,
                        "role": "OWNER",
                        "status": "ACTIVE"
                    },
                    {
                        "userId": 1,
                        "role": "READER",
                        "status": "ACTIVE"
                    }
                ],
                "excludeFromPublicDirectory": False,
                "diseaseFocusedResearch": True,
                "diseaseFocusedResearchName": "disease focused research name str 2",
                "otherPurposeDetails": "other purpose details str 2",
                "methodsDevelopment": False,
                "controlSet": False,
                "ancestry": False,
                "socialBehavioral": False,
                "populationHealth": False,
                "drugDevelopment": False,
                "commercialPurpose": False,
                "educational": False,
                "otherPurpose": False,
                "reasonForInvestigation": 'reasonForInvestigation string2',
                "intendToStudy": 'intendToStudy string2',
                "findingsFromStudy": 'findingsFromStudy string2'
            }
        ]

        self.send_post('workbench/directory/workspaces', request_data=request_json)

        # test get research projects directory
        result = self.send_get('researchHub/projectDirectory')
        self.assertEqual(len(result), 2)
        self.assertIn({'workspaceId': 0, 'name': 'workspace name str', 'creationTime': '2019-11-25T17:43:41.085000',
                       'modifiedTime': '2019-11-25T17:43:41.085000', 'status': 'ACTIVE',
                       'workspaceOwner': [{'userId': 1, 'userName': 'given name 2 family name 2',
                                           'affiliations': [{'institution': 'institution2',
                                                             'role': 'institution role 2',
                                                             'nonAcademicAffiliation': 'UNSET'},
                                                            {'institution': 'institution22',
                                                             'role': 'institution role 22',
                                                             'nonAcademicAffiliation': 'INDUSTRY'}]}],
                       'excludeFromPublicDirectory': True, 'diseaseFocusedResearch': True,
                       'diseaseFocusedResearchName': 'disease focused research name str',
                       'otherPurposeDetails': 'other purpose details str', 'methodsDevelopment': True,
                       'controlSet': True, 'ancestry': True, 'socialBehavioral': True, 'populationHealth': True,
                       'drugDevelopment': True, 'commercialPurpose': True, 'educational': True, 'otherPurpose': True,
                       'reasonForInvestigation': 'reasonForInvestigation string',
                       'intendToStudy': 'intendToStudy string',
                       'findingsFromStudy': 'findingsFromStudy string'
                       },
                      result)
        self.assertIn({'workspaceId': 1, 'name': 'workspace name str 2', 'creationTime': '2019-11-25T17:43:41.085000',
                       'modifiedTime': '2019-11-25T17:43:41.085000', 'status': 'INACTIVE',
                       'workspaceOwner': [{'userId': 0, 'userName': 'given name 1 family name 1',
                                           'affiliations': [{'institution': 'institution1',
                                                             'role': 'institution role 1',
                                                             'nonAcademicAffiliation': 'INDUSTRY'}]}],
                       'excludeFromPublicDirectory': False, 'diseaseFocusedResearch': True,
                       'diseaseFocusedResearchName': 'disease focused research name str 2',
                       'otherPurposeDetails': 'other purpose details str 2', 'methodsDevelopment': False,
                       'controlSet': False, 'ancestry': False, 'socialBehavioral': False, 'populationHealth': False,
                       'drugDevelopment': False, 'commercialPurpose': False, 'educational': False,
                       'otherPurpose': False, 'reasonForInvestigation': 'reasonForInvestigation string2',
                       'intendToStudy': 'intendToStudy string2',
                       'findingsFromStudy': 'findingsFromStudy string2'
                       },
                      result)

        # test get research projects directory with status
        result = self.send_get('researchHub/projectDirectory?status=ACTIVE')
        self.assertEqual(len(result), 1)
        self.assertIn({'workspaceId': 0, 'name': 'workspace name str', 'creationTime': '2019-11-25T17:43:41.085000',
                       'modifiedTime': '2019-11-25T17:43:41.085000', 'status': 'ACTIVE',
                       'workspaceOwner': [{'userId': 1, 'userName': 'given name 2 family name 2',
                                           'affiliations': [{'institution': 'institution2',
                                                             'role': 'institution role 2',
                                                             'nonAcademicAffiliation': 'UNSET'},
                                                            {'institution': 'institution22',
                                                             'role': 'institution role 22',
                                                             'nonAcademicAffiliation': 'INDUSTRY'}]}],
                       'excludeFromPublicDirectory': True, 'diseaseFocusedResearch': True,
                       'diseaseFocusedResearchName': 'disease focused research name str',
                       'otherPurposeDetails': 'other purpose details str', 'methodsDevelopment': True,
                       'controlSet': True, 'ancestry': True, 'socialBehavioral': True, 'populationHealth': True,
                       'drugDevelopment': True, 'commercialPurpose': True, 'educational': True, 'otherPurpose': True,
                       'reasonForInvestigation': 'reasonForInvestigation string',
                       'intendToStudy': 'intendToStudy string',
                       'findingsFromStudy': 'findingsFromStudy string'
                       },
                      result)
