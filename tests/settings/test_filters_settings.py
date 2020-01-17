"""
Test ability to validate filters-related settings.
"""
import pytest
import requests_mock

from tests.mocks import (
    mock_testfacility_user_response,
    MOCK_API_ENDPOINTS_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
)

from tests.fixtures import set_user_exp_dataset_config
from tests.utils import subtract


def test_filters_settings(set_user_exp_dataset_config):
    """Test ability to validate filters-related settings.
    """
    from mydata.conf import settings
    from mydata.models.settings.validation import validate_settings
    from mydata.logs import logger

    with requests_mock.Mocker() as mocker:
        list_api_endpoints_url = (
            "%s/api/v1/?format=json" % settings.general.mytardis_url
        )
        mocker.get(list_api_endpoints_url, text=MOCK_API_ENDPOINTS_RESPONSE)
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        )
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument"
            % settings.general.mytardis_url
        )
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        log_output = logger.get_value()

        validate_settings()

        expected_warning = "Files newer than 1 minute(s) are being ignored"
        assert expected_warning in subtract(logger.get_value(), log_output)

        old_value = settings.advanced.upload_invalid_user_or_group_folders
        settings.advanced.upload_invalid_user_or_group_folders = False
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "Invalid user folders are being ignored"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.advanced.upload_invalid_user_or_group_folders = old_value

        old_value1 = settings.advanced.upload_invalid_user_or_group_folders
        old_value2 = settings.advanced.folder_structure
        settings.advanced.upload_invalid_user_or_group_folders = False
        settings.advanced.folder_structure = "User Group / Experiment / Dataset"
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "Invalid user group folders are being ignored"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.advanced.upload_invalid_user_or_group_folders = old_value1
        settings.advanced.folder_structure = old_value2

        old_value1 = settings.filters.user_filter
        settings.filters.user_filter = "filter-string"
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "User folders are being filtered"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.filters.user_filter = old_value1

        old_value1 = settings.filters.user_filter
        old_value2 = settings.advanced.folder_structure
        settings.filters.user_filter = "filter-string"
        settings.advanced.folder_structure = "User Group / Experiment / Dataset"
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "User group folders are being filtered"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.filters.user_filter = old_value1
        settings.advanced.folder_structure = old_value2

        old_value = settings.filters.experiment_filter
        settings.filters.experiment_filter = "filter-string"
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "Experiment folders are being filtered"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.filters.experiment_filter = old_value

        old_value = settings.filters.dataset_filter
        settings.filters.dataset_filter = "filter-string"
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "Dataset folders are being filtered"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.filters.dataset_filter = old_value

        old_value = settings.filters.ignore_old_datasets
        settings.filters.ignore_old_datasets = True
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "Old datasets are being ignored"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.filters.ignore_old_datasets = old_value

        old_value = settings.filters.ignore_new_datasets
        settings.filters.ignore_new_datasets = True
        log_output = logger.get_value()
        validate_settings()
        expected_warning = "New datasets are being ignored"
        assert expected_warning in subtract(logger.get_value(), log_output)
        settings.filters.ignore_new_datasets = old_value

        def test_globs_validation(
            use_includes_file,
            use_excludes_file,
            includes_file,
            excludes_file,
            expected_warning=None,
            expected_exception_msg=None,
        ):
            """
            Test globs files settings validation / warnings
            """
            from mydata.conf import settings
            from mydata.models.settings.validation import validate_settings
            from mydata.utils.exceptions import InvalidSettings
            from mydata.logs import logger

            old_value1 = settings.filters.use_includes_file
            old_value2 = settings.filters.use_excludes_file
            old_value3 = settings.filters.includes_file
            old_value4 = settings.filters.excludes_file
            settings.filters.use_includes_file = use_includes_file
            settings.filters.use_excludes_file = use_excludes_file
            settings.filters.includes_file = includes_file
            settings.filters.excludes_file = excludes_file
            log_output = logger.get_value()
            if expected_exception_msg:
                with pytest.raises(InvalidSettings) as excinfo:
                    validate_settings()
                assert str(excinfo.value) == expected_exception_msg
            else:
                validate_settings()

            if expected_warning:
                assert expected_warning in subtract(logger.get_value(), log_output)
            settings.filters.use_includes_file = old_value1
            settings.filters.use_excludes_file = old_value2
            settings.filters.includes_file = old_value3
            settings.filters.excludes_file = old_value4

        warning = (
            "Only files matching patterns in includes "
            "file will be scanned for upload."
        )
        message = "No includes file was specified."
        test_globs_validation(
            use_includes_file=True,
            use_excludes_file=False,
            includes_file="",
            excludes_file="",
            expected_warning=warning,
            expected_exception_msg=message,
        )

        message = "Specified includes file doesn't exist."
        test_globs_validation(
            use_includes_file=True,
            use_excludes_file=False,
            includes_file="file/does/not/exist",
            excludes_file="",
            expected_warning=warning,
            expected_exception_msg=message,
        )

        message = "Specified includes file path is not a file."
        test_globs_validation(
            use_includes_file=True,
            use_excludes_file=False,
            includes_file=".",
            excludes_file="",
            expected_warning=warning,
            expected_exception_msg=message,
        )

        warning = (
            "Files matching patterns in excludes "
            "file will not be scanned for upload."
        )
        message = "No excludes file was specified."
        test_globs_validation(
            use_includes_file=False,
            use_excludes_file=True,
            includes_file="",
            excludes_file="",
            expected_warning=warning,
            expected_exception_msg=message,
        )

        warning = (
            "Files matching patterns in excludes "
            "file will not be scanned for upload, "
            "unless they match patterns in the includes file."
        )
        message = "No includes file was specified."
        test_globs_validation(
            use_includes_file=True,
            use_excludes_file=True,
            includes_file="",
            excludes_file="",
            expected_warning=warning,
            expected_exception_msg=message,
        )
