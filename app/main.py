"""Main script to run for streamlit app."""

import datetime as dt
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from requests.exceptions import HTTPError

from water_tracker import connectors, display

default_start_date = "2022-01-01"
default_end_date = "2022-12-31"
st.set_page_config(page_title="Water-Tracker", layout="wide")
st.title("Water-Tracker")

departements = [*list(range(1, 20)), "2A", "2B", *list(range(21, 96))]

code_departement = st.selectbox(
    label="Sélection du département",
    options=[str(dpt).zfill(2) for dpt in departements],
)
stations_connector = connectors.PiezoStationsConnector()
stations_params = {
    "code_departement": code_departement,
}
stations = stations_connector.retrieve(stations_params)

# Remove stations with measuring dates
has_no_start_measure_date = stations["date_debut_mesure"].isna()
has_no_end_measure_date = stations["date_fin_mesure"].isna()
has_no_measure_date = has_no_start_measure_date & has_no_end_measure_date
stations.drop(index=stations[has_no_measure_date].index, inplace=True)
# Replace unknown city names
unknown_name = stations["nom_commune"].isna()
stations.loc[unknown_name, "nom_commune"] = "Commune Inconnue"


def format_func(row_id: Any) -> str:
    """Format the bss code display name.

    Parameters
    ----------
    row_id : Any
        Index of the row to display the code of.

    Returns
    -------
    str
        'bss_code (city name)'
    """
    bss_code = stations.loc[row_id, "code_bss"]
    city_name = stations.loc[row_id, "nom_commune"]
    return f"{bss_code} ({city_name})"


bss_code_id = st.selectbox(
    label="Sélection du code bss de la station",
    options=stations.index,
    format_func=format_func,
)
bss_code = stations.loc[bss_code_id, "code_bss"]
min_date = stations.loc[bss_code_id, "date_debut_mesure"]
max_date = stations.loc[bss_code_id, "date_fin_mesure"]
col1, col2 = st.columns(2)
mesure_date_start = col1.date_input(
    label="Date de début de mesure",
    value=(max_date - dt.timedelta(days=365)),
    max_value=max_date,
    min_value=min_date,
)
if type(mesure_date_start) == dt.date:
    min_date_end = mesure_date_start
else:
    min_date_end = min_date

mesure_date_end = col2.date_input(
    label="Date de fin de mesure",
    value=max_date,
    max_value=max_date,
    min_value=min_date_end,
)

chronicle_connector = connectors.PiezoChroniclesConnector()
chronicles_params = {
    "code_bss": bss_code,
    "date_debut_mesure": mesure_date_start,
    "date_fin_mesure": mesure_date_end,
}
try:
    chronicles = chronicle_connector.retrieve(chronicles_params)
except HTTPError:
    message = "Echec de la connexion à l'API"
    figure = display.make_error_figure(
        message=message,
        title=f"Relevé Piézométrique de la station : {bss_code}",
        xtitle="Dates",
        ytitle="Niveau Nappe",
    )
else:
    if not chronicles.empty:
        scatter = go.Scatter(
            x=chronicles["date_mesure"],
            y=chronicles["niveau_nappe_eau"],
        )
        layout = go.Layout(
            title={"text": f"Relevé Piézométrique de la station : {bss_code}"},
            xaxis={"title": {"text": "Dates"}},
            yaxis={"title": {"text": "Niveau Nappe"}},
        )
        figure = go.Figure(
            data=[scatter],
            layout=layout,
        )
    else:
        figure = display.make_error_figure(
            message="Pas de données pour ce piézomètre.",
            title=f"Relevé Piézométrique de la station : {bss_code}",
            xtitle="Dates",
            ytitle="Niveau Nappe",
        )
st.plotly_chart(figure, use_container_width=True)
