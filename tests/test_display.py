"""Tests for the display tools."""

from water_tracker.display import make_error_figure


def test_make_error_figure() -> None:
    """Test that error figure is empty."""
    message = "error_message"
    title = "title"
    xtitle = "x"
    ytitle = "y"
    figure = make_error_figure(
        message=message,
        title=title,
        xtitle=xtitle,
        ytitle=ytitle,
    )
    assert not figure.data
