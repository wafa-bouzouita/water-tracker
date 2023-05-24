"""Display tools for the Chronicles."""

from typing import TYPE_CHECKING, Any

import pandas as pd
import plotly.graph_objects as go

if TYPE_CHECKING:
    from plotly.graph_objects import Scatter
    from streamlit.delta_generator import DeltaGenerator


class ChroniclesFigure:
    """Manage the plotly figure for the Chronicles Figure.

    Parameters
    ----------
    container : DeltaGenerator
        Container in which to plot the data.
    x_column : str
        Name of the x column.
    y_column : str
        Name of the y column.
    """

    def __init__(
        self,
        container: "DeltaGenerator",
        x_column: str,
        y_column: str,
        title: str = "",
    ) -> None:
        self.container = container
        self.x = x_column
        self.y = y_column
        self._traces: list["Scatter"] = []
        self.figure = go.Figure()
        self.title = title
        self._empty = False

    def add_error_annotation(self) -> None:
        """Create an empty figure with an error message."""
        self.figure.add_annotation(
            text="Not enough data.",
            showarrow=False,
            font={"size": 25},
        )

    @property
    def figure_traces(self) -> list["Scatter"]:
        """List of the figure traces."""
        return self._traces

    @property
    def empty_figure(self) -> bool:
        """Whether the figure is empty or not."""
        return self._empty

    @property
    def title(self) -> str:
        """Title of the Figure."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self.figure.layout = go.Layout(
            title={"text": value},
            xaxis={"title": {"text": self.x}},
            yaxis={"title": {"text": self.y}},
        )
        self._title = value

    def add_present_trace(
        self,
        chronicles_df: pd.DataFrame,
        **kwargs: Any | None,
    ) -> None:
        """Create the trace for the present data.

        Parameters
        ----------
        chronicles_df : pd.DataFrame
            DataFrame with present values.
        **kwargs: Any | None
            Additionnal parameters to pass to plotly.graph_objects.Scatter.
        """
        if chronicles_df.empty or self.empty_figure:
            self.add_error_annotation()
            self._empty = True
            return
        scatter = go.Scatter(
            x=chronicles_df[self.x],
            y=chronicles_df[self.y],
            **kwargs,
        )
        self._traces.append(scatter)

    def add_trend_trace(
        self,
        trend_df: pd.DataFrame,
        trend_column: str,
        **kwargs: Any | None,
    ) -> None:
        """Create the trace for the trend data.

        Parameters
        ----------
        trend_df : pd.DataFrame
            DataFrame with trend values.
        trend_column : str
            Name of the column with the trend.
        **kwargs: Any | None
            Additionnal parameters to pass to plotly.graph_objects.Scatter.
        """
        if trend_df.empty or self.empty_figure:
            return
        scatter = go.Scatter(
            x=trend_df[self.x],
            y=trend_df[trend_column],
            **kwargs,
        )
        self._traces.append(scatter)

    def display(self, **kwargs: Any) -> None:
        """Display the figure.

        Parameters
        ----------
        **kwargs: Any
            Additionnal parameters to pass to self.container.plotly_chart.
        """
        self.figure.add_traces(self.figure_traces)
        self.container.plotly_chart(self.figure, **kwargs)
