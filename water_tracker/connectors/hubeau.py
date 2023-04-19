"""Hubeau Connectors."""

from abc import ABC, abstractmethod
from typing import Tuple

import pandas as pd
import requests
import streamlit as st

from water_tracker.connectors.base import BaseConnector


@st.cache_data(ttl=24 * 60 * 60)
def retrieve_data_next_page(
    url: str,
    params: dict,
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


class HubeauConnector(BaseConnector, ABC):
    """Base class for Hubeau API Connectors."""

    @property
    @abstractmethod
    def url(self) -> str:
        """Url to which the request is made.

        Returns
        -------
        str
            Url
        """
        ...

    def _format_ouput(self, output: pd.DataFrame) -> pd.DataFrame:
        """Format the output of the request function retrieve_data_next_page.

        Parameters
        ----------
        output : pd.DataFrame
            Output of the API request made by retrieve_data_next_page.

        Returns
        -------
        pd.DataFrame
            Formatted dataframe.
        """
        df = output.copy()
        if self.columns_to_keep:
            df = df.filter(self.columns_to_keep, axis=1)
        # Converting 'dates' columns to datetime
        if self.date_columns:
            date_cols = self.date_columns
            df.loc[:, date_cols] = df.loc[:, date_cols].apply(pd.to_datetime)
        return df

    def retrieve(self, params: dict) -> pd.DataFrame:
        """Retrieve data.

        Parameters
        ----------
        params : dict
            Dictionary to send in the query string for the request.

        Returns
        -------
        pd.DataFrame
            Stations Dataframe which columns are \
            the one defined in self.columns_to_keep.
        """
        next_page = self.url
        dfs_all_pages = []
        while next_page != "":
            output, next_page = retrieve_data_next_page(next_page, params)
            # Filtering data using defined columns
            df = self._format_ouput(output)
            dfs_all_pages.append(df)
        return pd.concat(dfs_all_pages)


class PiezoStationsConnector(HubeauConnector):
    """Connector to retrieve Hubeau's piezometric stations data.

    Examples
    --------
    >>> from water_tracker import connectors
    >>> connector = connectors.PiezoStationsConnector
    >>> connector.retrieve(params=dict(code_departement="01"))
    """

    url: str = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
    columns_to_keep: list[str] = [
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
    date_columns: list[str] = [
        "date_debut_mesure",
        "date_fin_mesure",
    ]

    def retrieve(self, params: dict) -> pd.DataFrame:
        """Retrieve data from Hubeau Piezometric Stations API.

        Parameters
        ----------
        params : dict
            Parameters to use for the API request.

        Returns
        -------
        pd.DataFrame
            Output dataframe for the request.

        See Also
        --------
        https://hubeau.eaufrance.fr/page/api-piezometrie#/niveaux-nappes/stations
        for more informations on which parameters to use.
        """
        return super().retrieve(params)


class PiezoChroniclesConnector(HubeauConnector):
    """Connector to retrieve Hubeau's piezometric chronicles data.

    Examples
    --------
    >>> from water_tracker import connectors
    >>> connector = connectors.PiezoStationsConnector
    >>> connector.retrieve(params=dict(code_bss="07004X0046/D6-20"))
    """

    url: str = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
    columns_to_keep: list[str] = [
        "code_bss",
        "date_mesure",
        "niveau_nappe_eau",
        "qualification",
        "profondeur_nappe",
    ]
    date_columns: list[str] = [
        "date_mesure",
    ]

    def retrieve(self, params: dict) -> pd.DataFrame:
        """Retrieve data from Hubeau Piezometric Chronicles API.

        Parameters
        ----------
        params : dict
            Parameters to use for the API request.

        Returns
        -------
        pd.DataFrame
            Output dataframe for the request.

        See Also
        --------
        https://hubeau.eaufrance.fr/page/api-piezometrie#/niveaux-nappes/chroniques
        for more informations on which parameters to use.
        """
        return super().retrieve(params)
