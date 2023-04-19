"""Base classes for API connection module."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseConnector(ABC):
    """Base class for connectors."""

    @abstractmethod
    def retrieve(self, params: dict) -> pd.DataFrame:
        """Retrieve data using the connection to the API.

        Parameters
        ----------
        params : dict
            Parameters for the API request.

        Returns
        -------
        pd.DataFrame
            Formatted output.
        """
        ...

    @property
    @abstractmethod
    def columns_to_keep(self) -> list[str]:
        """List of columns to keep in the final dataframe.

        Returns
        -------
        list[str]
            Columns to keep
        """
        ...

    @property
    @abstractmethod
    def date_columns(self) -> list[str]:
        """List of columns to convert to datetime.

        Returns
        -------
        list[str]
            Dates columns.
        """
        ...

    @abstractmethod
    def _format_ouput(self, output: Any) -> pd.DataFrame:
        """Format the output of the request sending function.

        Parameters
        ----------
        output : Any
            Output from the API call.

        Returns
        -------
        pd.DataFrame
            Formatted DataFrame
        """
        ...
