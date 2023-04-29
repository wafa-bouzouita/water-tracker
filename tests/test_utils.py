"""Tests for the 'utils' objects."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from water_tracker import utils


@pytest.fixture()
def depts_json() -> list[dict]:
    """Fake input json.

    Returns
    -------
    list[dict]
        List of departments jsons.
    """
    return [
        {
            "num_dep": "01",
            "dep_name": "dep1",
            "region_name": "reg1",
        },
        {
            "num_dep": "02",
            "dep_name": "dep2",
            "region_name": "reg1",
        },
        {
            "num_dep": "10",
            "dep_name": "dep3",
            "region_name": "reg2",
        },
    ]


def test_load_dep_name_to_nb(
    depts_json: list[dict],
    mocker: MockerFixture,
) -> None:
    """Test that the returned json is correct.

    Parameters
    ----------
    depts_json : list[dict]
        Input json.
    mocker : MockerFixture
        Mocker for the json loading.
    """
    mocker.patch("water_tracker.utils.Path.open", return_value=None)
    mocker.patch("water_tracker.utils.json.load", return_value=depts_json)
    name_to_nb = utils.load_dep_name_to_nb(Path("path"))
    expected_output = {
        "dep1": "01",
        "dep2": "02",
        "dep3": "10",
    }
    assert name_to_nb == expected_output
