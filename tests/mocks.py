"""
tests/models/mocks.py

Mock MyTardis API responses which can be used in unit tests
"""
import copy
import json

EMPTY_LIST_RESPONSE_DICT = {
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 0,
    },
    "objects": [],
}

EMPTY_LIST_RESPONSE = json.dumps(EMPTY_LIST_RESPONSE_DICT)


def build_list_response(objects):
    """Build a mock API list response returning the specified objects
    """
    response_dict = copy.deepcopy(EMPTY_LIST_RESPONSE_DICT)
    response_dict["meta"]["total_count"] = len(objects)
    response_dict["objects"] = objects
    return json.dumps(response_dict)


MOCK_API_ENDPOINTS_RESPONSE = json.dumps(
    {
        "dataset": {
            "list_endpoint": "/api/v1/dataset/",
            "schema": "/api/v1/dataset/schema/",
        },
        "experiment": {
            "list_endpoint": "/api/v1/experiment/",
            "schema": "/api/v1/experiment/schema/",
        },
    }
)

MOCK_USER_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "username": "testfacility",
            "first_name": "TestFacility",
            "last_name": "RoleAccount",
            "email": "testfacility@example.com",
            "groups": [{"id": 1, "name": "test-facility-managers"}],
        }
    ]
)

MOCK_TESTUSER1_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "username": "testuser1",
            "first_name": "Test",
            "last_name": "User1",
            "email": "testuser1@example.com",
            "groups": [],
        }
    ]
)

MOCK_TESTUSER2_RESPONSE = MOCK_TESTUSER1_RESPONSE.replace("ser1", "ser2")

MOCK_GROUP_RESPONSE = build_list_response([{"id": 1, "name": "TestFacility-Group1"}])

MOCK_GROUP2_RESPONSE = MOCK_GROUP_RESPONSE.replace("Group1", "Group2")

MOCK_FACILITY_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "name": "Test Facility",
            "manager_group": {"id": 1, "name": "test-facility-managers"},
            "resource_uri": "/api/v1/facility/1/",
        }
    ]
)

MOCK_INSTRUMENT_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "name": "Test Instrument",
            "facility": {
                "id": 1,
                "name": "Test Facility",
                "manager_group": {"id": 1, "name": "test-facility-managers"},
            },
            "resource_uri": "/api/v1/instrument/1/",
        }
    ]
)

EXISTING_EXP_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "title": "Existing Experiment",
            "resource_uri": "/api/v1/experiment/1/",
        }
    ]
)

CREATED_EXP_RESPONSE = json.dumps(
    {"id": 1, "title": "Created Experiment", "resource_uri": "/api/v1/experiment/1/"}
)

EXP1_RESPONSE = json.dumps(
    {"id": 1, "title": "Exp1", "resource_uri": "/api/v1/experiment/1/"}
)

EXISTING_DATASET_RESPONSE = build_list_response(
    [{"id": 1, "description": "Existing Dataset"}]
)

CREATED_DATASET_RESPONSE = json.dumps(
    {"id": 1, "description": "Created Dataset", "resource_uri": "/api/v1/dataset/1/"}
)

MOCK_UPLOADER_RESPONSE = json.dumps(
    {"id": 1, "name": "Test Instrument", "resource_uri": "/api/v1/mydata_uploader/1/"}
)

MOCK_UPLOADER_WITH_SETTINGS = build_list_response(
    [
        {
            "id": 1,
            "name": "Test Instrument",
            "resource_uri": "/api/v1/mydata_uploader/1/",
            "settings_updated": "$settings_updated",
            "settings": [
                {"key": "instrument_name", "value": "Updated Instrument Name"},
                {"key": "facility_name", "value": "Updated Facility Name"},
                {"key": "contact_name", "value": "Updated Contact Name"},
                {"key": "contact_email", "value": "Updated.Contact.Email@example.com",},
                {"key": "ignore_new_files", "value": False},
                {"key": "ignore_new_files_minutes", "value": 0},
                {"key": "verification_delay", "value": 4.0},
                {"key": "connection_timeout", "value": "trigger ValueError"},
            ],
        }
    ]
)

MOCK_EXISTING_UPLOADER_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "name": "Test Instrument",
            "resource_uri": "/api/v1/mydata_uploader/1/",
        }
    ]
)

MOCK_URR_RESPONSE = build_list_response(
    [
        {
            "id": 1,
            "approved": True,
            "approved_storage_box": {
                "id": 1,
                "name": "staging-storage",
                "attributes": [
                    {"key": "scp_hostname", "value": "localhost"},
                    {"key": "scp_username", "value": "mydata"},
                    {"key": "scp_port", "value": "$scp_port"},
                ],
                "options": [{"key": "location", "value": "/path/to/upload/to/"}],
                "resource_uri": "/api/v1/storagebox/1/",
            },
            "resource_uri": "/api/v1/mydata_uploaderregistrationrequest/1/",
        }
    ]
)

CREATED_URR_RESPONSE = json.dumps(
    {
        "id": 1,
        "approved": False,
        "approved_storage_box": None,
        "resource_uri": "/api/v1/mydata_uploaderregistrationrequest/1/",
    }
)

MOCK_URR_MISSING_SBOX_ATTRS = build_list_response(
    [
        {
            "id": 1,
            "approved": True,
            "approved_storage_box": {
                "id": 1,
                "name": "staging-storage",
                "attributes": [],
                "options": [],
                "resource_uri": "/api/v1/storagebox/1/",
            },
            "resource_uri": "/api/v1/mydata_uploaderregistrationrequest/1/",
        }
    ]
)

VERIFIED_DATAFILE_RESPONSE = build_list_response(
    [
        {
            "id": 290386,
            "created_time": "2015-06-25T00:26:21",
            "datafile": None,
            "dataset": "/api/v1/dataset/1/",
            "deleted": False,
            "deleted_time": None,
            "directory": "",
            "filename": "Verified File",
            "md5sum": "0d2a8fb0a57bf4a9aabce5f7e69b36e9",
            "mimetype": "image/jpeg",
            "modification_time": None,
            "parameter_sets": [],
            "replicas": [
                {
                    "created_time": "2015-10-06T10:21:48.910470",
                    "datafile": "/api/v1/dataset_file/290386/",
                    "id": 444893,
                    "last_verified_time": "2015-10-06T10:21:53.952521",
                    "resource_uri": "/api/v1/replica/444893/",
                    "uri": "DatasetDescription-1/Verified File",
                    "verified": True,
                }
            ],
            "resource_uri": "/api/v1/mydata_dataset_file/290386/",
            "sha512sum": "",
            "size": "23",
            "version": 1,
        }
    ]
)


def mock_testfacility_user_response(mocker, mytardis_url):
    """Mock the list response for looking up a "testfacility" user
    """
    get_user_url = "%s/api/v1/user/?format=json&username=testfacility" % mytardis_url
    mocker.get(get_user_url, text=MOCK_USER_RESPONSE)


def mock_test_facility_response(mocker, mytardis_url):
    """Mock the list response for looking up a "Test Facility" facility
    """
    get_facility_url = "%s/api/v1/facility/?format=json" % mytardis_url
    mocker.get(get_facility_url, text=MOCK_FACILITY_RESPONSE)


def mock_test_instrument_response(mocker, mytardis_url):
    """Mock the list response for looking up "Test Instrument"
    """
    get_instrument_url = (
        "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument"
        % mytardis_url
    )
    mocker.get(get_instrument_url, text=MOCK_INSTRUMENT_RESPONSE)


def mock_testuser_response(mocker, mytardis_url, folder_structure, username):
    """Mock the list response for looking up "testuser1" or "testuser2" or "testuser3"

    folder_structure should begin with "Username" or "Email"
    """
    if username not in ("testuser1", "testuser2", "testuser3"):
        raise ValueError("Expecting 'testuser1' or 'testuser2' or 'testuser3'.")

    if not folder_structure.startswith("Username") and not folder_structure.startswith(
        "Email"
    ):
        raise ValueError("folder_structure should begin with Username or Email")

    if folder_structure.startswith("Username"):
        get_user_url = "%s/api/v1/user/?format=json&username=%s" % (
            mytardis_url,
            username,
        )
    else:
        get_user_url = "%s/api/v1/user/?format=json&email__iexact=%s%%40example.com" % (
            mytardis_url,
            username,
        )

    mock_user_response = MOCK_TESTUSER1_RESPONSE
    if username == "testuser2":
        mock_user_response = mock_user_response.replace("ser1", "ser2")
    if username == "testuser3":
        mock_user_response = mock_user_response.replace("ser1", "ser3")
    mocker.get(get_user_url, text=mock_user_response)


def mock_get_group(mocker, mytardis_url, group_name):
    """Mock the list response for looking up "TestFacility-Group1" or "TestFacility-Group2"
    """
    if group_name not in ("TestFacility-Group1", "TestFacility-Group2"):
        raise ValueError("Expecting 'TestFacility-Group1' or 'TestFacility-Group2'.")

    get_group_url = "%s/api/v1/group/?format=json&name=%s" % (mytardis_url, group_name)
    if group_name == "TestFacility-Group1":
        mock_group_response = MOCK_GROUP_RESPONSE
    else:
        mock_group_response = MOCK_GROUP2_RESPONSE
    mocker.get(get_group_url, text=mock_group_response)
