"""Main script to run for streamlit app."""

import datetime as dt

import numpy as np
import streamlit as st
from water_tracker import connectors
from water_tracker.display import chronicles
from water_tracker.transformers import trends

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
valid_stations = stations.drop(index=stations[has_no_measure_date].index)
# Replace unknown city names
unknown_name = valid_stations["nom_commune"].isna()
valid_stations.loc[unknown_name, "nom_commune"] = "Commune Inconnue"


def format_func(row_id: int) -> str:
    """Format the bss code display name.

    Parameters
    ----------
    row_id : int
        Index of the row to display the code of.

    Returns
    -------
    str
        'bss_code (city name)'
    """
    bss_code = valid_stations.loc[row_id, "code_bss"]
    city_name = valid_stations.loc[row_id, "nom_commune"]
    return f"{bss_code} ({city_name})"


bss_code_id = st.selectbox(
    label="Sélection du code bss de la station",
    options=valid_stations.index,
    format_func=format_func,
)
bss_code = valid_stations.loc[bss_code_id, "code_bss"]
min_date = valid_stations.loc[bss_code_id, "date_debut_mesure"]
max_date = valid_stations.loc[bss_code_id, "date_fin_mesure"]
col1, col2 = st.columns(2)
default = max((max_date - dt.timedelta(days=365)), min_date)
mesure_date_start = col1.date_input(
    label="Date de début de mesure",
    value=default,
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

# Chronicles

# Trend Thresholds

insufficient = trends.TrendThreshold("insufficient", np.nan, 3)
bad = trends.TrendThreshold("bad", 3, 5)
correct = trends.TrendThreshold("correct", 5, 10)
good = trends.TrendThreshold("good", 10, 15)
very_good = trends.TrendThreshold("very good", 15, 25)
excellent = trends.TrendThreshold("excellent", 25, np.nan)

trend_eval = trends.TrendEvaluation(
    insufficient,
    bad,
    correct,
    good,
    very_good,
    excellent,
)

trend_props = trends.TrendProperties(
    measure_start=min_date.date(),
    measure_end=max_date.date(),
)


chronicle_connector = connectors.PiezoChroniclesConnector()
chronicles_params = {
    "code_bss": bss_code,
    "date_debut_mesure": mesure_date_start,
    "date_fin_mesure": mesure_date_end,
}
chronicles_df = chronicle_connector.retrieve(chronicles_params)
display_trend = False
if not trend_props.has_enough_data:
    st.error("Données insuffisantes pour calculer une tendance.")
else:
    eval_result = trend_eval.evaluate(trend=trend_props)
    if eval_result == insufficient.return_value:
        st.error("Données insuffisantes pour calculer une tendance.")
    elif eval_result == bad.return_value:
        st.warning(
            "La tendance ne peut pas être considérée "
            "fiable du fait du manque de données.",
        )
        display_trend = st.checkbox("Afficher la tendance.", value=False)
    else:
        st.success(
            f"Tendance calculée sur {trend_props.nb_years_history} "
            f"année{'s' if trend_props.nb_years_history > 1 else ''}.",
        )
        display_trend = st.checkbox("Afficher la tendance.", value=True)

chronicles_display = chronicles.ChroniclesFigure(
    container=st,
    x_column="date_mesure",
    y_column="niveau_nappe_eau",
    title=f"Relevé Piézométrique de la station : {bss_code}",
)
chronicles_display.add_present_trace(
    chronicles_df=chronicles_df,
    name="Mesures Actuelles",
    marker={"color": "blue"},
)
if display_trend:
    trend = trends.AverageTrend()
    history_params = {
        "code_bss": bss_code,
        "date_debut_mesure": trend_props.trend_data_start,
        "date_fin_mesure": trend_props.trend_data_end,
    }
    history = chronicle_connector.retrieve(history_params)
    trend_df = trend.transform(
        historical_df=history,
        present_df=chronicles_df,
        dates_column="date_mesure",
        values_column="niveau_nappe_eau",
    )
    chronicles_display.add_trend_trace(
        trend_df,
        trend.mean_values_column,
        name="Mesures Moyennes",
        marker={"color": "black"},
    )
chronicles_display.display(use_container_width=True)
