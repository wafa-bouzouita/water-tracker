"""Hubeau Connectors."""

from typing import Tuple

import pandas as pd
import requests
import streamlit as st


@st.cache_data(ttl=24 * 60 * 60)
def retrieve_data_next_page(
    url: str, params: dict
) -> Tuple[pd.DataFrame, str]:
    """Retrieve data from a given url and with the given parameters.

    Parameters
    ----------
    url : str
        Url to request
    params : dict
        Dictionary to send in the query string for the Request

    Returns
    -------
    Tuple[pd.DataFrame, str]
        Result DataFrame, next page url ("" if last)
    """
    response = requests.get(url, params)
    response.raise_for_status()
    response_json = response.json()
    # Checking whether the page is the last or not
    if "next" not in response_json.keys():
        next_page = ""
    elif response_json["next"] is None:
        next_page = ""
    else:
        next_page = response_json["next"]
    df = pd.DataFrame.from_dict(response_json["data"])
    return df, next_page


class PiezoConnector:
    """Connector class to retrieve piezometric data from \
    https://hubeau.eaufrance.fr/page/api-piezometrie.

    Examples
    --------
    Load stations data:
    >>> url = "http://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
    >>> params = {"code_departement": "01"}
    >>> connector = PiezoConnector()
    >>> df = connector.retrieve_stations(url=url, params=params)

    Load chronicles data:
    >>> url = "http://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
    >>> params = {"code_bss": "06533X0070/F2","size": "5000",}
    >>> connector = PiezoConnector()
    >>> df = connector.retrieve_chronicles(url=url, params=params)
    """

    stations_columns: list[str] = [
        "code_bss",
        "date_debut_mesure",
        "date_fin_mesure",
        "code_commune_insee",
        "nom_commune",
        "bss_id",
        "code_departement",
        "nom_departement",
        "nb_mesure_piezo",
        "code_masse_eau",
    ]
    stations_date_columns: list[str] = [
        "date_debut_mesure",
        "date_fin_mesure",
    ]
    chronicles_columns: list[str] = [
        "code_bss",
        "date_mesure",
        "niveau_nappe_eau",
        "qualification",
        "profondeur_nappe",
    ]
    chronicles_date_columns: list[str] = [
        "date_mesure",
    ]

    def __init__(self) -> None:
        pass

    def retrieve_stations(self, url: str, params: dict) -> pd.DataFrame:
        """Retrieve stations data.

        Parameters
        ----------
        url : str
            Url to request
        params : dict
            Dictionary to send in the query string for the Request

        Returns
        -------
        pd.DataFrame
            Stations Dataframe which columns are \
            the one defined in self.stations_columns.
        """
        next_page = url
        dfs_all_pages = []
        while next_page != "":
            df, next_page = retrieve_data_next_page(next_page, params)
            # Filtering data using defined columns
            if self.stations_columns:
                df = df.filter(self.stations_columns, axis=1)
            # Converting 'dates' columns to datetime
            if self.stations_date_columns:
                date_cols = self.stations_date_columns
                df.loc[:, date_cols] = df.loc[:, date_cols].apply(
                    pd.to_datetime
                )
            dfs_all_pages.append(df)
        return pd.concat(dfs_all_pages)

    def retrieve_chronicles(self, url: str, params: dict) -> pd.DataFrame:
        """Retrieve chronicles data.

        Parameters
        ----------
        url : str
            Url to request
        params : dict
            Dictionary to send in the query string for the Request

        Returns
        -------
        pd.DataFrame
            Chronicles Dataframe which columns are \
            the one defined in self.chronicles_columns.
        """
        next_page = url
        dfs_all_pages = []
        while next_page != "":
            df, next_page = retrieve_data_next_page(next_page, params)
            # Filtering data using defined columns
            if self.chronicles_columns:
                df = df.filter(self.chronicles_columns, axis=1)
                # Converting 'dates' columns to datetime
            if self.chronicles_date_columns:
                date_cols = self.chronicles_date_columns
                df.loc[:, date_cols] = df.loc[:, date_cols].apply(
                    pd.to_datetime
                )
            dfs_all_pages.append(df)
        return pd.concat(dfs_all_pages)
