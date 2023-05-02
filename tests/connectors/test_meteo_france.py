"""Tests for Meteo France connectors."""

import pandas as pd
import pytest
from pytest_mock import MockerFixture
from water_tracker.connectors.meteo_france import (
    PrecipitationsMFConnector,
    SSWIMFConnector,
)


@pytest.fixture()
def precip_connector(
    mocker: MockerFixture,
) -> PrecipitationsMFConnector:
    """Meteo France Precipitation Connector fixture.

    Parameters
    ----------
    mocker : MockerFixture
        Mocker fixture.

    Returns
    -------
    PrecipitationsMFConnector
        Precipitation Connector.
    """
    mocker.patch(
        "water_tracker.connectors.meteo_france.load_dep_name_to_nb",
        return_value=None,
    )
    dept_mapping = {
        "dept1": "01",
        "dept2": "10",
    }
    precip_connector = PrecipitationsMFConnector()
    precip_connector.dept_mapping = dept_mapping
    precip_connector.columns_to_keep = {
        "column1": "column",
        "zone": "zone_map",
    }
    precip_connector.zone_column = "zone_map"
    return precip_connector


@pytest.fixture()
def sswi_connector() -> SSWIMFConnector:
    """Meteo France SSWI Connector Fixture.

    Returns
    -------
    SSWIMFConnector
        Meteo France SSWI Connector
    """
    return SSWIMFConnector()


def test_format_ouput_zone_mapping(
    precip_connector: PrecipitationsMFConnector,
) -> None:
    """Test the zone renamning in format output.

    Parameters
    ----------
    precip_connector : PrecipitationsMFConnector
        Precipitation Connector Fixture.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "zone": ["dept1", "dept2", "dept3"],
        },
    )
    output_df = precip_connector.format_output(input_df)
    expected_columns = list(precip_connector.columns_to_keep.values())
    assert (output_df.columns == expected_columns).all()
    assert (output_df["zone_map"] == ["01", "10", "dept3"]).all()


def test_precip_retrieve(
    precip_connector: PrecipitationsMFConnector,
    mocker: MockerFixture,
) -> None:
    """Test the retrieve method for the Meteo France Precipitation Connector.

    Parameters
    ----------
    precip_connector : PrecipitationsMFConnector
        Precipitation Connector Fixture.
    mocker : MockerFixture
        Mocker Fixture.
    """
    precip_connector.zone_column = "zone_map"
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "zone": ["dept1", "dept2", "dept3"],
        },
    )
    mocker.patch(
        "water_tracker.connectors.meteo_france.pd.read_csv",
        return_value=input_df,
    )
    output_df = precip_connector.retrieve({})
    expected_columns = list(precip_connector.columns_to_keep.values())
    assert (output_df.columns == expected_columns).all()
    assert (output_df["zone_map"] == ["01", "10", "dept3"]).all()


def test_sswi_retrieve(
    sswi_connector: SSWIMFConnector,
    mocker: MockerFixture,
) -> None:
    """Test the retrieve method for the SSWI connector.

    Parameters
    ----------
    sswi_connector : SSWIMFConnector
        SSWI Connector.
    mocker : MockerFixture
        Mocker fixture.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
        },
    )
    sswi_connector.columns_to_keep = {}
    mocker.patch(
        "water_tracker.connectors.meteo_france.pd.read_csv",
        return_value=input_df,
    )
    ouput_df = sswi_connector.retrieve({})
    assert ouput_df.equals(input_df)
