"""Tests for copernicus connectors."""

import pandas as pd
import pytest
import xarray as xr
from pytest_mock import MockerFixture
from water_tracker.connectors.copernicus import (
    PrecipitationsERA5Connector,
    default_area,
    default_days,
    default_months,
    default_times,
    default_years,
)


@pytest.fixture()
def connector() -> PrecipitationsERA5Connector:
    """PrecipitationsERA5Connector connector."""
    return PrecipitationsERA5Connector()


def test_make_request_default(connector: PrecipitationsERA5Connector) -> None:
    """Test make request default values.

    Parameters
    ----------
    connector : PrecipitationsERA5Connector
        Connector to use for the request.
    """
    request = connector.make_request()
    assert request["product_type"] == connector.product_type
    assert request["variable"] == connector.variable
    assert request["format"] == connector.file_format
    assert request["year"] == default_years
    assert request["month"] == default_months
    assert request["day"] == default_days
    assert request["time"] == default_times
    assert request["area"] == default_area


def test_retrieve_success(
    mocker: MockerFixture,
    connector: PrecipitationsERA5Connector,
) -> None:
    """Test retrieve with a successful response.

    Parameters
    ----------
    mocker : MockerFixture
        Mocxker Fixture.
    connector : PrecipitationsERA5Connector
        Connector to use for the request.
    """
    mocker.patch("cdsapi.Client.retrieve")
    raw_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": [1, 2, 3],
            "time": [
                "2023-01-01 00:00:00",
                "2023-01-01 01:00:00",
                "2023-01-01 02:00:00",
            ],
        },
    )
    mocker.patch("cdsapi.api.Client.retrieve", return_value=None)
    mocker.patch("xarray.open_dataset", return_value=xr.Dataset())
    mocker.patch("xarray.Dataset.to_dataframe", return_value=pd.DataFrame())
    mocker.patch("pandas.DataFrame.reset_index", return_value=raw_df)
    connector.columns_to_keep = ["column1", "time"]
    connector.date_columns = ["time"]
    output_df = connector.retrieve({})
    assert (output_df.columns == connector.columns_to_keep).all()
    assert output_df.dtypes["time"] == "datetime64[ns]"


def test_retrieve_fail(
    mocker: MockerFixture,
    connector: PrecipitationsERA5Connector,
) -> None:
    """Test retrieve with a successful response.

    Parameters
    ----------
    mocker : MockerFixture
        Mocxker Fixture.
    connector : PrecipitationsERA5Connector
        Connector to use for the request.
    """
    mocker.patch("cdsapi.Client.retrieve", side_effect=Exception)
    connector.columns_to_keep = ["column1", "time"]
    connector.date_columns = ["time"]
    output_df = connector.retrieve({})
    assert (output_df.columns == connector.columns_to_keep).all()
    assert output_df.dtypes["time"] == "datetime64[ns]"
