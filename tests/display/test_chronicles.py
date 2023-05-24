"""Tests for chronicles-related display tools."""

from unittest.mock import Mock

import pandas as pd
from water_tracker.display import chronicles


def test_figure_title() -> None:
    """Test the title attribution for the ChroniclesFigure."""
    mock_container = Mock()
    display = chronicles.ChroniclesFigure(
        container=mock_container,
        x_column="column1",
        y_column="column2",
        title="title",
    )
    assert display.title == "title"
    display.title = "title2"
    assert display.title == "title2"


def test_empty_present() -> None:
    """Test empty property if empty present dataframe."""
    empty_df = pd.DataFrame(
        {
            "column1": [],
            "column2": [],
        },
    )
    mock_container = Mock()
    display = chronicles.ChroniclesFigure(
        container=mock_container,
        x_column="column1",
        y_column="column2",
        title="title",
    )
    display.add_present_trace(empty_df)
    assert display.empty_figure
    assert not display.figure_traces


def test_empty_trend() -> None:
    """Test empty property if empty trend dataframe."""
    empty_df = pd.DataFrame(
        {
            "column1": [],
            "column2": [],
            "column3": [],
        },
    )
    mock_container = Mock()
    display = chronicles.ChroniclesFigure(
        container=mock_container,
        x_column="column1",
        y_column="column2",
        title="title",
    )
    display.add_trend_trace(empty_df, "column3")
    assert not display.empty_figure
    assert not display.figure_traces


def test_add_present_trace() -> None:
    """Test add_present_trace."""
    present_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": [1, 2, 3],
        },
    )
    mock_container = Mock()
    display = chronicles.ChroniclesFigure(
        container=mock_container,
        x_column="column1",
        y_column="column2",
        title="title",
    )
    display.add_present_trace(present_df)
    assert len(display.figure_traces) == 1


def test_add_trend_trace() -> None:
    """Test add_trend_trace."""
    trend_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": [1, 2, 3],
            "column3": [1, 2, 3],
        },
    )
    mock_container = Mock()
    display = chronicles.ChroniclesFigure(
        container=mock_container,
        x_column="column1",
        y_column="column2",
        title="title",
    )
    display.add_trend_trace(trend_df, "column3")
    assert len(display.figure_traces) == 1


def test_present_trend_trace() -> None:
    """Test trend and present addition trace."""
    trend_present_df = pd.DataFrame(
        {
            "column1": [1, 2, 3],
            "column2": [1, 2, 3],
            "column3": [1, 2, 3],
        },
    )
    mock_container = Mock()
    display = chronicles.ChroniclesFigure(
        container=mock_container,
        x_column="column1",
        y_column="column2",
        title="title",
    )
    display.add_present_trace(trend_present_df)
    display.add_trend_trace(trend_present_df, "column3")
    expected_lengh = 2
    assert len(display.figure_traces) == expected_lengh
