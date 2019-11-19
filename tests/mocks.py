"""
tests/models/mocks.py

Mock MyTardis API responses which can be used in unit tests
"""
import json

MOCK_API_ENDPOINTS_RESPONSE = json.dumps({
    "dataset": {
        "list_endpoint": "/api/v1/dataset/",
        "schema": "/api/v1/dataset/schema/"
    },
    "experiment": {
        "list_endpoint": "/api/v1/experiment/",
        "schema": "/api/v1/experiment/schema/"
    }
})

MOCK_USER_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "username": "testfacility",
        "first_name": "TestFacility",
        "last_name": "RoleAccount",
        "email": "testfacility@example.com",
        "groups": [{
            "id": 1,
            "name": "test-facility-managers"
        }]
    }]
})

MOCK_TESTUSER1_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "username": "testuser1",
        "first_name": "Test",
        "last_name": "User1",
        "email": "testuser1@example.com",
        "groups": []
    }]
})

MOCK_TESTUSER2_RESPONSE = MOCK_TESTUSER1_RESPONSE.replace("ser1", "ser2")

MOCK_GROUP_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "name": "TestFacility-Group1",
    }]
})

MOCK_GROUP2_RESPONSE = MOCK_GROUP_RESPONSE.replace("Group1", "Group2")

MOCK_FACILITY_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "name": "Test Facility",
        "manager_group": {
            "id": 1,
            "name": "test-facility-managers"
        },
        "resource_uri": "/api/v1/facility/1/"
    }]
})

MOCK_INSTRUMENT_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "name": "Test Instrument",
        "facility": {
            "id": 1,
            "name": "Test Facility",
            "manager_group": {
                "id": 1,
                "name": "test-facility-managers"
            }
        },
        "resource_uri": "/api/v1/instrument/1/"
    }]
})

EXISTING_EXP_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "title": "Existing Experiment",
        "resource_uri": "/api/v1/experiment/1/"
    }]
})

CREATED_EXP_RESPONSE = json.dumps({
    "id": 1,
    "title": "Created Experiment",
    "resource_uri": "/api/v1/experiment/1/"
})

EXP1_RESPONSE = json.dumps({
    "id": 1,
    "title": "Exp1",
    "resource_uri": "/api/v1/experiment/1/"
})


EMPTY_LIST_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 0
    },
    "objects": []
})

EXISTING_DATASET_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "description": "Existing Dataset"
    }]
})

CREATED_DATASET_RESPONSE = json.dumps({
    "id": 1,
    "description": "Created Dataset",
    "resource_uri": "/api/v1/dataset/1/"
})

MOCK_UPLOADER_RESPONSE = json.dumps({
    "id": 1,
    "name": "Test Instrument",
    "resource_uri": "/api/v1/mydata_uploader/1/"
})

MOCK_UPLOADER_WITH_SETTINGS = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
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
            {"key": "progress_poll_interval", "value": 2.0},
            {"key": "connection_timeout", "value": "trigger ValueError"},
        ]
    }]
})

MOCK_EXISTING_UPLOADER_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "name": "Test Instrument",
        "resource_uri": "/api/v1/mydata_uploader/1/"
    }]
})

MOCK_URR_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "approved": True,
        "approved_storage_box": {
            "id": 1,
            "name": "staging-storage",
            "attributes": [
                {
                    "key": "scp_hostname",
                    "value": "localhost",
                },
                {
                    "key": "scp_username",
                    "value": "mydata",
                },
                {
                    "key": "scp_port",
                    "value": "$scp_port"
                }
            ],
            "options": [
                {
                    "key": "location",
                    "value": "/path/to/upload/to/"
                }
            ],
            "resource_uri": "/api/v1/storagebox/1/"
        },
        "resource_uri": "/api/v1/mydata_uploaderregistrationrequest/1/"
    }]
})

CREATED_URR_RESPONSE = json.dumps({
    "id": 1,
    "approved": False,
    "approved_storage_box": None,
    "resource_uri": "/api/v1/mydata_uploaderregistrationrequest/1/"
})

MOCK_URR_MISSING_SBOX_ATTRS = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 1
    },
    "objects": [{
        "id": 1,
        "approved": True,
        "approved_storage_box": {
            "id": 1,
            "name": "staging-storage",
            "attributes": [
            ],
            "options": [
            ],
            "resource_uri": "/api/v1/storagebox/1/"
        },
        "resource_uri": "/api/v1/mydata_uploaderregistrationrequest/1/"
    }]
})
