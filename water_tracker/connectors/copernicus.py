"""Copernicus Connectors."""

import os
from typing import TYPE_CHECKING

import cdsapi
import pandas as pd
import xarray as xr
from dotenv import load_dotenv

if TYPE_CHECKING:
    from cdsapi.api import Client

# Load the environment variables
load_dotenv()

default_product_type: str = "reanalysis"
default_variables: list[str] = ["total_precipitation"]
default_format: str = "netcdf"
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


class ERA5Connector:
    """Connector class to retrieve data from \
    https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview.\
    Data is downloaded from the provider and saved in a file using the cdsapi\
    library. Data is then read and converted as a pandas DataFrame.

    Parameters
    ----------
    reload : bool, optional
        Whether to reload the data even if th etarget file laready exist.
        , by default True

    Examples
    --------
    Load with default request parameters
    >>> connector = copernicus.ERA5Connector()
    >>> request = connector.make_request()
    >>> df = connector.retrieve_data(product, request, target)

    Load potential evaporation and total evaporation with other default \
    parameters
    >>> connector = copernicus.ERA5Connector()
    >>> request = connector.make_request(
    ...     variables=[
    ...         "potential_evaporation",
    ...         "total_evaporation",
    ...     ]
    ... )
    >>> df = connector.retrieve_data(product, request, target)
    """

    # Initialize a connector using the cdsapi.Client object
    client: "Client" = cdsapi.Client(verify=True)

    def __init__(self, reload=True) -> None:
        self.reload = reload

    def _retrieve(
        self,
        dataset_id: str,
        request: dict,
        target: str,
    ) -> None:
        """Retrieve data from the given dataset, with the right parameters \
        and saves it to the 'target' file.

        Parameters
        ----------
        dataset_id : str
            Name of the dataset to collect data from.
        request : dict
            Parameters for the API call.
        target : str
            Filepath to save the API data to.
        """
        # Check if the file already exists
        if not self.reload and os.path.isfile(target):
            return
        self.client.retrieve(
            name=dataset_id,
            request=request,
            target=target,
        )

    def make_request(
        self,
        product_type: str = default_product_type,
        variables: list[str] = default_variables,
        format: str = default_format,
        years: list[int] = default_years,
        months: list[int] = default_months,
        days: list[int] = default_days,
        times: list[str] = default_times,
        area: list[float] = default_area,
    ) -> dict:
        """Make the request dictionnary for the API call.

        Parameters
        ----------
        product_type : str, optional
            Name of the product to collect data from.
            , by default default_product_type
        variable : str, optional
            List of variables to get., by default default_variable
        format : str, optional
            Format of the downloaded data., by default default_format
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
        request = {
            "product_type": product_type,
            "variable": variables,
            "format": format,
            "year": years,
            "month": months,
            "day": days,
            "time": times,
            "area": area,
        }
        return request

    def retrieve_data(
        self,
        dataset_id: str,
        request: dict,
        target: str,
    ) -> pd.DataFrame:
        """Retrieve data.

         Parameters
        ----------
        dataset_id : str
            Name of the dataset to collect data from.
        request : dict
            Parameters for the API call.
        target : str
            Filepath to save the API data to.

        Returns
        -------
        pd.DataFrame
            DataFrame from the dataset.
        """
        # Collect the data and saves it to the target file
        self._retrieve(
            dataset_id=dataset_id,
            request=request,
            target=target,
        )
        # Loads data from the target file
        df = xr.open_dataset(target).to_dataframe().reset_index()
        return df
