from base_standard_index import BaseStandardIndex
from datetime import date, timedelta, datetime
from water_tracker import WaterTracker
def main():
    # Remplacez 'votre_cle_api' par votre clé API réelle
    api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZWEzNTMxYzU4ZTk0OThkMTgxZWRkMjUwZmZmY2I0MmY0MDY1MjA1OWMyZjc1OTRlZGI1MWViZGU5MWUyYjMyYjMwNzIwNDkxNTQ1NzNkNjUiLCJpYXQiOjE3MDE5MzkyNjAuNTk4OTQ0LCJuYmYiOjE3MDE5MzkyNjAuNTk4OTQ4LCJleHAiOjE3MDMyMzUyNjAuNTkzNDk1LCJzdWIiOiIxOTIzMCIsInNjb3BlcyI6W119.enNMLF4idv-BFxcTYCzHIITkohsfg2UcNwxI7tkGTzYeklXny54sclnl2KGaDFYSYTmm8WSYkKq4tM5El5fYvbXyF75lTuCUg6kWdQaIXdLA7Xcf0G_P2AXzVUeIVx0AhhCjKBdT7r6RxtoPzh5HrXUi7cvFxnGhHaDKx67M_WXehSNzM417FHp-DXtHqGDB5QP98RDIPHwf8vcRmFo1DXFpN1xQTYrclWftfRamBh3cc4iZJ1oZ_xLrph72Mu96vcMtuleSfug-Yzwb2DZdUQOnbDL2zgFbYrvglA6IMtfv_hOw7lNPrapb69oME_RdIu3T-ZbGvpLppSmo_JpR8sLKz03pwVEFCJhCcb0mAqSeAqXXfDY4BQ1chouGoRFgCUeIp9ScbB6qOurr-BNnoW-xgX7zipm7jepW_yxnvhJGBaN-tr-8GWewgQvZ87OC5rXyTsq9oWHxa_8j2wdPBCydgMNBrDhbTdhFR4nbRUaEFV4FqYUAK0eBwWbrspR4yeOyFwBM7xp6jR7YTebFnBYIrbDLo4rKeAuQee5M2V6MXM2hH44_4QMkXjvJLnLK5m_qDVnguRIusmrPm3I8brDsMqFaSyZFzg1Fj51ngL6KSEr-mjyxL0fsLkQT25ydoU7hzZ4T4mqRH7C7gp993n03pY8TgBA6Alwc8L3q0do"
    
    indicateur = ["nappes", "pluviométrie"]

    # Créez une instance de la classe WaterTracker
    wt = WaterTracker(api_key)


    # If you haven't built station data and downloaded all timeseries yet uncomment the following lines to do so
    #wt.build_stations_data()
    #wt.download_all_timeseries()

    # For each indicator, load existing data and generate the plot
    for indicateur in indicateur:
        # Comment the following line if you don't want to recalculate standardized indicators on each run
        wt.process(indicateur=indicateur)

        # Load existing data
        wt.load()

        # Generate the plot for drought distribution in France
        wt.plot_counts_france(indicateur=indicateur)


if __name__ == "__main__":
    main()
