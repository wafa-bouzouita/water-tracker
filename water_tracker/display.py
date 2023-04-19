"""Generic Display tools for the streamlit app."""

import plotly.graph_objects as go


def make_error_figure(
    message: str,
    title: str = "",
    xtitle: str = "",
    ytitle: str = "",
) -> go.Figure:
    """Create an empty figure with an error message.

    Parameters
    ----------
    message : str
        Message to write in the figure.
    title : str, optional
        Title of the figure., by default ""
    xtitle : str, optional
        Title of the x axis., by default ""
    ytitle : str, optional
        Title of the y axis., by default ""

    Returns
    -------
    go.Figure
        Empty figure with the message written inside.
    """
    layout = go.Layout(
        title={"text": title},
        xaxis={"title": {"text": xtitle}},
        yaxis={"title": {"text": ytitle}},
    )
    figure = go.Figure(
        data=[],
        layout=layout,
    )
    figure.add_annotation(
        text=message,
        showarrow=False,
        font={"size": 25},
    )
    return figure
