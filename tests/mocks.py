"""
tests/models/mocks.py

Mock MyTardis API responses which can be used in unit tests
"""
import copy
import json

from string import Template

from urllib.parse import quote


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
                {"key": "contact_email", "value": "Updated.Contact.Email@example.com"},
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


def mock_testuser_response(mocker, settings, username):
    """Mock the list response for looking up "testuser1" or "testuser2" or "testuser3"

    folder_structure should begin with "Username" or "Email"
    """
    if username not in ("testuser1", "testuser2", "testuser3"):
        raise ValueError("Expecting 'testuser1' or 'testuser2' or 'testuser3'.")

    mytardis_url = settings.general.mytardis_url
    folder_structure = settings.advanced.folder_structure

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


def mock_testusers_response(mocker, settings, usernames):
    """Mock the list responses for looking up a list of usernames
    """
    for username in usernames:
        mock_testuser_response(mocker, settings, username)


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


def mock_birds_flowers_dataset_creation(mocker, settings):
    """Mock the creation of the Birds and Flowers datasets used in tests
    """
    # A partial query-string match can be used for mocking:
    get_birds_dataset_url = (
        "/api/v1/dataset/?format=json&experiments__id=1&description=Birds"
    )
    mocker.get(get_birds_dataset_url, text=EMPTY_LIST_RESPONSE)
    get_flowers_dataset_url = (
        "/api/v1/dataset/?format=json&experiments__id=1&description=Flowers"
    )
    mocker.get(
        get_flowers_dataset_url,
        text=EXISTING_DATASET_RESPONSE.replace("Existing Dataset", "Flowers"),
    )

    post_dataset_url = "%s/api/v1/dataset/" % settings.general.mytardis_url
    # Response really should be different for each dataset,
    # but that would complicate mocking:
    mocker.post(post_dataset_url, text=CREATED_DATASET_RESPONSE)


def mock_birds_flowers_datafile_lookups(mocker):
    """Mock the lookups of the Birds and Flowers datafiles used in tests
    """
    # A partial query-string match can be used for mocking:
    for filename in (
        "1024px-Colourful_flowers.JPG",
        "Flowers_growing_on_the_campus_of_Cebu_City_National_Science_High_School.jpg",
        "Pond_Water_Hyacinth_Flowers.jpg",
    ):
        get_datafile_url = (
            "/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=%s"
            % filename
        )
        mocker.get(
            get_datafile_url,
            text=VERIFIED_DATAFILE_RESPONSE.replace("Verified File", filename),
        )
    for filename in (
        "1024px-Australian_Birds_%40_Jurong_Bird_Park_%284374195521%29.jpg",
    ):
        get_datafile_url = (
            "/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=%s"
            % filename
        )
        mocker.get(get_datafile_url, text=EMPTY_LIST_RESPONSE)
    for filename in ("Black-beaked-sea-bird-close-up.jpg",):
        get_datafile_url = (
            "/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=%s"
            % filename
        )
        error_response = json.dumps({"error_message": "Internal Server Error"})
        mocker.get(get_datafile_url, text=error_response, status_code=500)

    post_datafile_url = "/api/v1/mydata_dataset_file/"
    mocker.post(post_datafile_url, status_code=201)


def mock_exp_creation(mocker, settings, title, user_folder_name):
    """Mock the creation of experiments and their ObjectACLs
    """
    get_exp_url = (
        "%s/api/v1/mydata_experiment/?format=json"
        "&title=%s"
        "&folder_structure=%s&user_folder_name=%s"
    ) % (
        settings.general.mytardis_url,
        quote(title),
        quote(settings.advanced.folder_structure),
        quote(user_folder_name),
    )
    mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
    post_experiment_url = "%s/api/v1/mydata_experiment/" % settings.general.mytardis_url
    mocker.post(post_experiment_url, text=CREATED_EXP_RESPONSE)
    post_objectacl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
    mocker.post(post_objectacl_url, status_code=201)


def mock_uploader_creation_response(mocker, settings):
    """Mock the creation of MyData's Uploader record
    """
    get_uploader_url = (
        "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
    ) % settings.general.mytardis_url
    mocker.get(get_uploader_url, text=EMPTY_LIST_RESPONSE)
    post_uploader_url = ("%s/api/v1/mydata_uploader/") % settings.general.mytardis_url
    mocker.post(post_uploader_url, text=MOCK_UPLOADER_RESPONSE)


def mock_uploader_update_response(mocker, settings):
    """Mock updating an Uploader record when MyData is run again
    """
    get_uploader_url = (
        "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
    ) % settings.general.mytardis_url
    mocker.get(get_uploader_url, text=MOCK_EXISTING_UPLOADER_RESPONSE)
    put_uploader_url = ("%s/api/v1/mydata_uploader/1/") % settings.general.mytardis_url
    mocker.put(put_uploader_url, text=MOCK_UPLOADER_RESPONSE)


def mock_get_urr(mocker, settings, key_fingerprint, scp_port):
    """Mock getting an existing uploader registration request
    """
    get_urr_url = (
        "%s/api/v1/mydata_uploaderregistrationrequest/?format=json"
        "&uploader__uuid=00000000001&requester_key_fingerprint=%s"
    ) % (settings.general.mytardis_url, key_fingerprint)
    mocker.get(
        get_urr_url, text=Template(MOCK_URR_RESPONSE).substitute(scp_port=scp_port)
    )


def mock_invalid_user_response(mocker, settings):
    """Mock looking up an invalid user
    """
    get_invalid_user_url = (
        "%s/api/v1/user/?format=json&username=INVALID_USER"
    ) % settings.general.mytardis_url
    mocker.get(get_invalid_user_url, text=EMPTY_LIST_RESPONSE)
