"""Tests for base connectors."""

import pandas as pd
import pytest
from water_tracker.connectors.hubeau import PiezoChroniclesConnector


@pytest.fixture()
def chronicles_connector() -> PiezoChroniclesConnector:
    """Instanciate a PiezoChroniclesConnector object.

    Returns
    -------
    PiezoChroniclesConnector
        Instanciated object.
    """
    return PiezoChroniclesConnector()


def test_format_output_date(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test date output format.

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "date1": ["2022-01-01", None, "1980-01-01"],
            "date2": [None, "2022-02-01", "2021-01-30"],
        },
    )
    columns_to_keep = {"date1": "date1", "date3": "date3"}
    expected_columns = list(columns_to_keep.values())
    chronicles_connector.columns_to_keep = columns_to_keep
    date_columns = ["date1", "date3"]
    chronicles_connector.date_columns = date_columns
    output_df = chronicles_connector.format_output(input_df)
    dtypes = output_df.dtypes
    assert (output_df.columns == expected_columns).all()
    assert dtypes["date1"] == "datetime64[ns]"
    assert dtypes["date3"] == "datetime64[ns]"
    assert output_df["date3"].isna().all()


def test_format_output_date_different_date_format(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test date output format.

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "date1": ["20200101", None, "19800101"],
            "date2": [None, "20200201", "20210130"],
        },
    )
    columns_to_keep = {"date1": "date1", "date3": "date3"}
    expected_columns = list(columns_to_keep.values())
    chronicles_connector.columns_to_keep = columns_to_keep
    date_columns = ["date1", "date3"]
    chronicles_connector.date_columns = date_columns
    output_df = chronicles_connector.format_output(
        input_df,
        date_format="%Y%m%d",
    )
    dtypes = output_df.dtypes
    assert (output_df.columns == expected_columns).all()
    assert dtypes["date1"] == "datetime64[ns]"
    assert dtypes["date3"] == "datetime64[ns]"
    assert output_df["date3"].isna().all()


def test_format_output_no_date(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test output format (without considering dates).

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "column3": ["a", "b", "c"],
        },
    )
    columns_keep = {
        "column1": "column1",
        "column2": "column2",
        "column4": "column4",
    }
    expected_columns = list(columns_keep.values())
    chronicles_connector.columns_to_keep = columns_keep
    chronicles_connector.date_columns = []
    output_df = chronicles_connector.format_output(input_df)
    assert (output_df.columns == expected_columns).all()
    assert (output_df["column1"] == input_df["column1"]).all()
    assert (output_df["column2"] == input_df["column2"]).all()
    assert output_df["column4"].isna().all()


def test_columns_renaming(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test output format columns renaming.

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "column3": ["a", "b", "c"],
        },
    )
    columns_keep = {
        "column1": "column5",
        "column2": "column2",
        "column4": "column3",
    }
    expected_columns = list(columns_keep.values())
    chronicles_connector.columns_to_keep = columns_keep
    chronicles_connector.date_columns = []
    output_df = chronicles_connector.format_output(input_df)
    assert (output_df.columns == expected_columns).all()
    assert (output_df["column5"] == input_df["column1"]).all()
    assert (output_df["column2"] == input_df["column2"]).all()
    assert output_df["column3"].isna().all()


def test_format_output_empty_columns_to_keep(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test output format when returning all input columns.

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "column3": ["a", "b", "c"],
            "date1": [None, "2022-02-01", "2021-01-30"],
        },
    )
    columns_keep: dict = {}
    date_columns: list = []
    chronicles_connector.columns_to_keep = columns_keep
    chronicles_connector.date_columns = date_columns
    output_df = chronicles_connector.format_output(input_df)
    assert output_df.equals(input_df)


def test_format_output_date_and_values(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test output format with both date and other values.

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "column3": ["a", "b", "c"],
            "date1": [None, "2022-02-01", "2021-01-30"],
        },
    )
    columns_keep: dict[str, str] = {
        "column1": "column1",
        "column2": "column2",
        "date2": "date2",
    }
    expected_columns = list(columns_keep.values())
    date_columns: list = ["date1", "date2"]
    chronicles_connector.columns_to_keep = columns_keep
    chronicles_connector.date_columns = date_columns
    output_df = chronicles_connector.format_output(input_df)
    assert (output_df.columns == expected_columns).all()
    assert (output_df["column1"] == input_df["column1"]).all()
    assert (output_df["column2"] == input_df["column2"]).all()
    assert output_df.dtypes["date2"] == "datetime64[ns]"
    assert output_df["date2"].isna().all()


def test_format_output_date_and_values_empty(
    chronicles_connector: PiezoChroniclesConnector,
) -> None:
    """Test output format with all data types and keeping all columns.

    Parameters
    ----------
    chronicles_connector : PiezoChroniclesConnector
        Connector to use format_output from.
    """
    input_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "column3": ["a", "b", "c"],
            "date1": [None, "2022-02-01", "2021-01-30"],
        },
    )
    columns_keep: dict = {}
    date_columns: list = ["date1", "date2"]
    chronicles_connector.columns_to_keep = columns_keep
    chronicles_connector.date_columns = date_columns
    output_df = chronicles_connector.format_output(input_df)
    assert (output_df.columns == input_df.columns).all()
    assert (output_df["column1"] == input_df["column1"]).all()
    assert (output_df["column2"] == input_df["column2"]).all()
    assert output_df.dtypes["date1"] == "datetime64[ns]"
