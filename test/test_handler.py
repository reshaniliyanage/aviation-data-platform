import pytest
from unittest.mock import patch

from handler import validate_weather, fetch_with_retry


def test_validate_weather_success():
    data = {"current_weather": {"temperature": 10}}
    assert validate_weather(data) is True


def test_validate_weather_failure():
    with pytest.raises(ValueError):
        validate_weather({})


@patch("handler.requests.get")
def test_fetch_with_retry(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"current_weather": {}}

    result = fetch_with_retry("fake_url")
    assert "current_weather" in result