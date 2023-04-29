"""Copernicus Connectors."""

import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import cdsapi
import pandas as pd
import xarray as xr
from cdsapi.api import Client
from dotenv import load_dotenv

from water_tracker.connectors.base import BaseConnector

# Load the environment variables
load_dotenv()

default_years: list[int] = [2023]
default_months: list[int] = [1]
default_days: list[int] = [1]
default_times: list[str] = [
    "00:00",
    "01:00",
    "02:00",
    "03:00",
    "04:00",
    "05:00",
    "06:00",
    "07:00",
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
    "21:00",
    "22:00",
    "23:00",
]
default_area: list[float] = [
    46.33,
    0.78,
    47.30,
    2.28,
]


class BaseERA5Connector(BaseConnector, ABC):
    """Connector class to retrieve data from Copernicus.

    Data is retrieved from:
    https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview.

    Data is downloaded from the provider and saved in a file using the cdsapi\
    library. Data is then read and converted as a pandas DataFrame.

    Parameters
    ----------
    reload : bool, optional
        Whether to reload the data even if th etarget file laready exist.
        , by default True
    """

    client: Client = cdsapi.Client(
        verify=True,
        url=os.environ.get("CDSAPI_URL"),
        key=os.environ.get("CDSAPI_KEY"),
    )
    name: str = "reanalysis-era5-land"
    product_type: str = "reanalysis"
    file_format: str = "netcdf"

    def __init__(self, reload: bool = True) -> None:
        self.reload = reload

    @property
    @abstractmethod
    def variable(self) -> str:
        """Variable to collect from the Dataset.

        Returns
        -------
        str
            Variable name.
        """

    def make_request(
        self,
        years: list[int] = default_years,
        months: list[int] = default_months,
        days: list[int] = default_days,
        times: list[str] = default_times,
        area: list[float] = default_area,
    ) -> dict:
        """Make the request dictionnary for the API call.

        Parameters
        ----------
        year : list[int], optional
            List of years to collect., by default default_year
        month : list[int], optional
            List of months to collect., by default default_month
        day : list[int], optional
            List of days to collect., by default default_day
        time : list[str], optional
            List of hours to collect., by default default_time
        area : list[float], optional
            Boundaries of the area to collect data for.
            , by default default_area

        Returns
        -------
        dict
            Request dictionnary.
        """
        # Request dictionnary definition
        return {
            "product_type": self.product_type,
            "variable": self.variable,
            "format": self.file_format,
            "year": years,
            "month": months,
            "day": days,
            "time": times,
            "area": area,
        }

    def retrieve(
        self,
        params: dict,
    ) -> pd.DataFrame:
        """Retrieve data.

        Parameters
        ----------
        request : dict
            Parameters for the API call.

        Returns
        -------
        pd.DataFrame
            DataFrame from the dataset.
        """
        # Download the file in a named temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=".",
            suffix=".nc",
        ) as file:
            try:
                self.client.retrieve(
                    name=self.name,
                    request=params,
                    target=file.name,
                )
            except Exception:  # noqa: BLE001
                raw_df = pd.DataFrame()
            else:
                # Loads data from the target file
                dataset = xr.open_dataset(file.name)
                dataset_df = dataset.to_dataframe()
                raw_df = dataset_df.reset_index()
            # Close the temporary file
            file.close()
            Path.unlink(Path(file.name))
        return self.format_output(raw_df)

    def format_output(
        self,
        raw_df: pd.DataFrame,
        date_format: str | None = None,
    ) -> pd.DataFrame:
        """Format the output of the request function retrieve_data_next_page.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Output of the API request made by retrieve_data_next_page.
        date_format: str | None
            Date format to pass to pd.to_datetime.

        Returns
        -------
        pd.DataFrame
            Formatted dataframe.
        """
        return super().format_output(raw_df, date_format=date_format)


class PrecipitationsERA5Connector(BaseERA5Connector):
    """Connector for total Precipitation Data Collection.

    Examples
    --------
    >>> from water_tracker.connectors import PrecipitationsERA5Connector
    >>> params = connector.make_request()
    >>> df = connector.retrieve(params)
    """

    variable: str = "total_precipitation"

    columns_to_keep: dict[str, str] = {
        "longitude": "longitude",
        "latitude": "latitude",
        "time": "time",
        "tp": "tp",
    }
    date_columns: list[str] = ["time"]

    def retrieve(
        self,
        params: dict,
    ) -> pd.DataFrame:
        """Retrieve total precipitation data from Copernicus ERA5 land dataset.

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
        https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview
        for more informations on which parameters to use.
        """
        return super().retrieve(params)
