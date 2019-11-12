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
        }
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
        }
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

EXP1_RESPONSE = json.dumps({
    "id": 1,
    "title": "Exp1",
    "resource_uri": "/api/v1/experiment/1/"
})


EMPTY_EXP_RESPONSE = json.dumps({
    "meta": {
        "limit": 20,
        "next": None,
        "offset": 0,
        "previous": None,
        "total_count": 0
    },
    "objects": []
})

MOCK_EXISTING_DATASET_RESPONSE = json.dumps({
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
