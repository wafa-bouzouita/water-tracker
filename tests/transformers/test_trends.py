"""Tests for Trends transformers."""

import datetime as dt
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from water_tracker.transformers.trends import (
    AverageTrend,
    ExistingColumnNameError,
    ThresholdError,
    TrendEvaluation,
    TrendProperties,
    TrendThreshold,
)


# Trend Properties Test


@pytest.mark.parametrize(
    ("measure_start", "measure_end", "not_in_trend", "min_trend", "expected"),
    [
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 1, 1, True),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 5, 5, False),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 0, 4, True),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 4, 0, True),
        (dt.date(2020, 1, 1), dt.date(2015, 1, 1), 1, 1, False),
    ],
)
def test_has_enough_data(
    measure_start: dt.datetime,
    measure_end: dt.datetime,
    not_in_trend: int,
    min_trend: int,
    expected: bool,
) -> None:
    """Test the TrendProperties.has_enough_data value.

    Parameters
    ----------
    measure_start : dt.datetime
        First date of measure.
    measure_end : dt.datetime
        LAst date of measure.
    not_in_trend : int
        Number of years not in the trend.
    min_trend : int
        Minimal number of years for the trend.
    expected : bool
        Expected result.
    """
    trend = TrendProperties(
        measure_start=measure_start,
        measure_end=measure_end,
        years_not_in_trend=not_in_trend,
        min_trend_length_year=min_trend,
    )
    assert trend.has_enough_data == expected


@pytest.mark.parametrize(
    ("start", "end", "not_in_trend", "min_trend", "expected_end"),
    [
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 1, 1, dt.date(2019, 1, 1)),
        (dt.date(2010, 1, 1), dt.date(2020, 1, 1), 4, 1, dt.date(2016, 1, 1)),
    ],
)
def test_trend_boundaries(
    start: dt.date,
    end: dt.date,
    not_in_trend: int,
    min_trend: int,
    expected_end: dt.date,
) -> None:
    """Test the boundaries date for the trend.

    Parameters
    ----------
    start : dt.date
        Mesaure starting date.
    end : dt.date
        Measure Ending date.
    not_in_trend : int
        Number of years not in the trend.
    min_trend : int
        Minimal number of years in the trend.
    expected_end : dt.date
        Exepected value for the trend ending date.
    """
    trend_prop = TrendProperties(
        measure_start=start,
        measure_end=end,
        years_not_in_trend=not_in_trend,
        min_trend_length_year=min_trend,
    )
    assert trend_prop.trend_data_start == start
    assert trend_prop.trend_data_end == expected_end


@pytest.mark.parametrize(
    ("start", "end", "not_in_trend", "min_trend"),
    [
        (dt.date(2015, 1, 1), dt.date(2014, 1, 1), 1, 1),
        (dt.date(2015, 1, 1), dt.date(2016, 1, 1), 4, 1),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 4, 3),
    ],
)
def test_trend_none_boundaries(
    start: dt.date,
    end: dt.date,
    not_in_trend: int,
    min_trend: int,
) -> None:
    """Test for None trend boundaries date.

    Parameters
    ----------
    start : dt.date
        Measure starting date.
    end : dt.date
        Measure ending date.
    not_in_trend : int
        Number of years not in the trend.
    min_trend : int
        Minimal number of years in the trend.
    """
    trend_prop = TrendProperties(
        measure_start=start,
        measure_end=end,
        years_not_in_trend=not_in_trend,
        min_trend_length_year=min_trend,
    )
    assert trend_prop.trend_data_start is None
    assert trend_prop.trend_data_end is None


@pytest.mark.parametrize(
    ("start", "end", "not_in_trend", "min_trend", "expected"),
    [
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 1, 1, 4),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 3, 1, 2),
        (dt.date(2017, 1, 1), dt.date(2020, 1, 1), 1, 1, 2),
        (dt.date(2020, 1, 1), dt.date(2015, 1, 1), 1, 1, 0),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 1, 10, 0),
        (dt.date(2015, 1, 1), dt.date(2020, 1, 1), 10, 1, 0),
    ],
)
def test_nb_years_history(
    start: dt.date,
    end: dt.date,
    not_in_trend: int,
    min_trend: int,
    expected: int,
) -> None:
    """Test for the number of years.

    Parameters
    ----------
    start : dt.date
        Measure starting date.
    end : dt.date
        Measure ending date.
    not_in_trend : int
        Number of years not in the trend.
    min_trend : int
        Minimal number of years in the trend.
    expected : int
        Expected number of years.
    """
    trend_prop = TrendProperties(
        measure_start=start,
        measure_end=end,
        years_not_in_trend=not_in_trend,
        min_trend_length_year=min_trend,
    )
    assert trend_prop.nb_years_history == expected


# Trend Threshold Test


@pytest.mark.parametrize(
    ("minimum_value", "value", "expected"),
    [
        (1, 0, False),
        (2, 3, True),
        (np.nan, 3, True),
    ],
)
def test_threshold_minimum(
    minimum_value: float,
    value: float,
    expected: bool,
) -> None:
    """Test for the minimal bound assertion of the TrendThreshold.

    Parameters
    ----------
    minimum_value : float
        Minimum value to verify.
    value : float
        Value to test.
    expected : bool
        Expected value.
    """
    threshold = TrendThreshold(
        return_value="test",
        minimum_value=minimum_value,
        maximum_value=np.nan,
    )
    assert threshold.verifies_minimum(value) == expected


@pytest.mark.parametrize(
    ("maximum_value", "value", "expected"),
    [
        (1, 0, True),
        (2, 3, False),
        (np.nan, 3, True),
    ],
)
def test_threshold_maximum(
    maximum_value: float,
    value: float,
    expected: bool,
) -> None:
    """Test for the maximum bound assertion of the TrendThreshold.

    Parameters
    ----------
    maximum_value : float
        Maximum value to verify.
    value : float
        Value to test.
    expected : bool
        Expected value.
    """
    threshold = TrendThreshold(
        return_value="test",
        minimum_value=np.nan,
        maximum_value=maximum_value,
    )
    assert threshold.verifies_maximum(value) == expected


@pytest.mark.parametrize(
    ("nb_years_history", "minimum_value", "maximum_value", "expected"),
    [
        (1.2, 1, 3, True),
        (1, 3, 5, False),
        (7, 2, 6, False),
        (-3, -5, 3, True),
        (-3, -2, 3, False),
        (-5.8, -6, -5, True),
        (-3, -6, -5, False),
        (3.9, np.nan, 7, True),
        (9, np.nan, 7, False),
        (3.9, 2, np.nan, True),
        (1, 2, np.nan, False),
    ],
)
def test_is_in_threshold(
    nb_years_history: float,
    minimum_value: float,
    maximum_value: float,
    expected: bool,
) -> None:
    """Test the is_in_threshold method of TrendThreshold.

    Parameters
    ----------
    nb_years_history : float
        Number of years of history for the Mock TrendProperty.
    minimum_value : float
        Threshold lower bound.
    maximum_value : float
        Threshold upper bound.
    expected : bool
        Expected value.
    """
    trend_prop_mock = Mock(TrendProperties)
    trend_prop_mock.nb_years_history = nb_years_history
    threshold = TrendThreshold(
        return_value="test",
        minimum_value=minimum_value,
        maximum_value=maximum_value,
    )
    assert threshold.is_in_threshold(trend_prop_mock) == expected


# Trend Evaluation Test
@pytest.mark.parametrize(
    ("threshold1", "threshold2", "nb_years", "expected"),
    [
        (TrendThreshold("t1", 0, 3), TrendThreshold("t2", 3, 5), 2.2, "t1"),
        (TrendThreshold("t1", 0, 3), TrendThreshold("t2", 3, 5), 0, "t1"),
        (TrendThreshold("t1", 0, 3), TrendThreshold("t2", 0, 5), 2.2, "t1"),
        (TrendThreshold("t2", 0, 5), TrendThreshold("t1", 0, 3), 2.2, "t2"),
        (
            TrendThreshold("t1", np.nan, 5),
            TrendThreshold("t2", 3, 5),
            2.2,
            "t1",
        ),
    ],
)
def test_evaluate_threshold(
    threshold1: TrendThreshold,
    threshold2: TrendThreshold,
    nb_years: float,
    expected: bool,
) -> None:
    """Test the TrendEvaluation.evaluate method.

    Parameters
    ----------
    threshold1 : TrendThreshold
        First threshold.
    threshold2 : TrendThreshold
        Second Threshold.
    nb_years : float
        Number of years for the TrendProperties.
    expected : bool
        Exepected result.
    """
    trend_prop_mock = Mock(TrendProperties)
    trend_prop_mock.nb_years_history = nb_years
    trend_eval = TrendEvaluation(
        threshold1,
        threshold2,
    )
    assert trend_eval.evaluate(trend_prop_mock) == expected


@pytest.mark.parametrize(
    ("threshold1", "threshold2", "nb_years"),
    [
        (TrendThreshold("t1", 0, 3), TrendThreshold("t2", 5, 10), 4.2),
        (TrendThreshold("t1", 0, 3), TrendThreshold("t2", 3, 5), -1),
        (TrendThreshold("t1", 0, 3), TrendThreshold("t1", 3, 5), 5),
        (TrendThreshold("t1", 0, 3), TrendThreshold("t1", 3, 5), 7),
        (TrendThreshold("t1", 0, 3), TrendThreshold("t2", 3, 5), np.nan),
    ],
)
def test_evaluate_error(
    threshold1: TrendThreshold,
    threshold2: TrendThreshold,
    nb_years: float,
) -> None:
    """Test the error for TrendEvaluation if number of year not in thresholds.

    Parameters
    ----------
    threshold1 : TrendThreshold
        First threshold.
    threshold2 : TrendThreshold
        Second Threshold.
    nb_years : float
        Number of years for the TrendProperties.
    """
    trend_prop_mock = Mock(TrendProperties)
    trend_prop_mock.nb_years_history = nb_years
    trend_eval = TrendEvaluation(
        threshold1,
        threshold2,
    )
    with pytest.raises(ThresholdError):
        trend_eval.evaluate(trend_prop_mock)


# AverageTrend Test


@pytest.mark.parametrize(
    ("remove", "expected"),
    [
        (
            False,
            pd.DataFrame(
                {
                    "column1": [1, 2, 3, 4],
                    "date1": ["20220101", "20200703", "20000101", "20250401"],
                    AverageTrend.day_of_year_column: [1, 185, 1, 91],
                },
            ),
        ),
        (
            True,
            pd.DataFrame(
                {
                    "column1": [1, 2, 3, 4],
                    AverageTrend.day_of_year_column: [1, 185, 1, 91],
                },
            ),
        ),
    ],
)
def test_add_days_of_year_column(
    remove: bool,
    expected: pd.DataFrame,
) -> None:
    """Test AverageTrend's day of year computation.

    Parameters
    ----------
    remove : bool
        Whether to remove the date column or not.
    expected : pd.DataFrame
        Expected output for the method.
    """
    trend = AverageTrend()
    dates_df = pd.DataFrame(
        {
            "column1": [1, 2, 3, 4],
            "date1": ["20220101", "20200703", "20000101", "20250401"],
        },
    )
    output_df = trend.add_days_of_year_column(dates_df, "date1", remove)
    assert output_df.equals(expected)


def test_add_days_of_year_column_error() -> None:
    """Test error raising for add_days_of_year_column method."""
    trend = AverageTrend()
    dates_df = pd.DataFrame(
        {
            "column1": [1, 2, 3, 4],
            "date1": ["20220101", "20200703", "20000101", "20250401"],
            trend.day_of_year_column: [1, 2, 3, 4],
        },
    )
    with pytest.raises(ExistingColumnNameError):
        trend.add_days_of_year_column(dates_df, "date1", False)


def test_compute_reference_values() -> None:
    """Test average values computation."""
    trend = AverageTrend()
    history = pd.DataFrame(
        {
            trend.day_of_year_column: [1, 1, 2, 3, 4, 4, 4],
            "values": [1, 2, 3, 4, 5, 6, 7],
            "column1": [1, 1, 1, 1, 1, 1, 1],
            "column2": ["a", "a", "a", "a", "a", "a", "a"],
        },
    )
    expected_df = pd.DataFrame(
        {
            trend.day_of_year_column: [1, 2, 3, 4],
            "column1": [1.0, 1.0, 1.0, 1.0],
            trend.mean_values_column: [1.5, 3, 4, 6],
        },
    )
    output_df = trend.compute_reference_values(history, "values")
    assert output_df.equals(expected_df)


def test_transform() -> None:
    """Test transform method."""
    trend = AverageTrend()
    history = pd.DataFrame(
        {
            "d1": ["20100101", "20110101", "20100105", "20100616", "20100105"],
            "values": [1, 2, 3, 4, 5],
            "column1": [1, 1, 1, 1, 1],
        },
    )
    present = pd.DataFrame(
        {
            "column1": [1, 2, 3, 4],
            "d1": ["20220101", "20200105", "20000101", "20250401"],
            "values": [1, 3, 5, 7],
        },
    )
    expected = pd.DataFrame(
        {
            "column1": [1, 2, 3, 4],
            "d1": ["20220101", "20200105", "20000101", "20250401"],
            "values": [1, 3, 5, 7],
            AverageTrend.day_of_year_column: [1, 5, 1, 91],
            AverageTrend.mean_values_column: [1.5, 4, 1.5, np.nan],
        },
    )
    output_df = trend.transform(history, present, "d1", "values")
    assert output_df.equals(expected)
