"""Base classes for API connection module."""

from abc import ABC, abstractmethod

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

    @property
    @abstractmethod
    def columns_to_keep(self) -> dict[str, str]:
        """List of columns to keep in the final dataframe.

        Returns
        -------
        list[str]
            Columns to keep
        """

    @property
    @abstractmethod
    def date_columns(self) -> list[str]:
        """List of columns to convert to datetime.

        Returns
        -------
        list[str]
            Dates columns.
        """

    def format_ouput(
        self,
        output: pd.DataFrame,
        date_format: str | None,
    ) -> pd.DataFrame:
        """Format the output of the request function retrieve_data_next_page.

        Parameters
        ----------
        output : pd.DataFrame
            Output of the API request made by retrieve_data_next_page.
        date_format: str | None
            Date format to pass to pd.to_datetime.

        Returns
        -------
        pd.DataFrame
            Formatted dataframe.
        """
        response_df = output.copy()
        columns_to_keep = self.columns_to_keep.keys()
        # Converting 'dates' columns to datetime
        for column in self.date_columns:
            if column in response_df.columns:
                date_col = response_df.pop(column)
                response_df[column] = pd.to_datetime(
                    date_col,
                    format=date_format,
                )
            elif column in columns_to_keep:
                response_df[column] = pd.NaT
        if columns_to_keep:
            response_df = response_df.reindex(columns=columns_to_keep)
            response_df = response_df.rename(columns=self.columns_to_keep)
        return response_df
