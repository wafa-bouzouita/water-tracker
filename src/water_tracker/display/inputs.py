"""Inputs objects."""

import datetime as dt
from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import pandas as pd

from water_tracker.display.defaults import (
    DefaultDate,
    DefaultDepartement,
    DefaultInput,
    DefaultMaxDate,
    DefaultMinDate,
    DefaultStation,
)

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator
    from streamlit.elements.time_widgets import DateWidgetReturn


DefaultInputT = TypeVar("DefaultInputT", bound="DefaultInput")


class BaseInput(ABC, Generic[DefaultInputT]):
    """Base class for inputs.

    Parameters
    ----------
    label : str
        Label for the input object.
    default_input : DefaultInputT
        Default Input object.
    """

    def __init__(
        self,
        label: str,
        default_input: DefaultInputT,
    ) -> None:
        self.label = label
        self._default = default_input

    @abstractmethod
    def build(self, container: "DeltaGenerator") -> Any | None:
        """Build the input.

        Parameters
        ----------
        container : DeltaGenerator
            Container to build the input object to.

        Returns
        -------
        Any | None
            Input value.
        """


class DepartmentInput(BaseInput[DefaultDepartement]):
    """Departments inputs.

    Parameters
    ----------
    label : str
        Label for the input object.
    default_input : DefaultInputT
        Default Input object.
    """

    @cached_property
    def options(self) -> list[str]:
        """Inputs options."""
        return [
            *map(DepartmentInput.format_dept, range(1, 20)),
            *["2A", "2B"],
            *map(DepartmentInput.format_dept, range(21, 96)),
        ]

    @staticmethod
    def format_dept(dept_nb: int) -> str:
        """Format departements numbers.

        Parameters
        ----------
        dept_nb : int
            Departement number.

        Returns
        -------
        str
            Formatted department number (1 -> '01', 10 -> '10', '2A' -> '2A').
        """
        return str(dept_nb).zfill(2)

    def build(self, container: "DeltaGenerator") -> str | None:
        """Build the input in a given container.

        Parameters
        ----------
        container : DeltaGenerator
            Container to build the input object to.

        Returns
        -------
        str | None
            Input value.
        """
        return container.selectbox(
            label=self.label,
            options=self.options,
            index=self.options.index(self._default.value),
        )


class StationInput(BaseInput[DefaultStation]):
    """Stations Input.

    Parameters
    ----------
    label : str
        Label for the input object.
    stations_df : pd.DataFrame
        Stations DataFrame.
    default_input : DefaultInputT
        Default Input object.
    """

    def __init__(
        self,
        label: str,
        stations_df: pd.DataFrame,
        default_input: DefaultStation,
        bss_field_name: str = "code_bss",
        city_field_name: str = "nom_commune",
    ) -> None:
        super().__init__(label, default_input)
        self._stations = stations_df
        self._bss_field_name = bss_field_name
        self._city_field_name = city_field_name

    @property
    def stations(self) -> pd.DataFrame:
        """Stations used for the input."""
        return self._stations

    @property
    def options(self) -> list[int]:
        """Input Options."""
        return self._stations.index.to_list()

    def format_func(self, row_index: int) -> str:
        """Format function to apply to stations dataframe index.

        Parameters
        ----------
        row_index : int
            Index of a row.

        Returns
        -------
        str
            Formatted string to display.
        """
        bss_code = self._stations.loc[row_index, self._bss_field_name]
        city_name = self._stations.loc[row_index, self._city_field_name]
        return f"{bss_code} ({city_name})"

    def build(self, container: "DeltaGenerator") -> int | None:
        """Build the input in a given container.

        Parameters
        ----------
        container : DeltaGenerator
            Container to build the input object to.

        Returns
        -------
        int | None
            Input value.
        """

        def format_func(row_index: int) -> str:
            return self.format_func(row_index=row_index)

        return container.selectbox(
            label=self.label,
            options=self.options,
            index=self.options.index(self._default.value),
            format_func=format_func,
        )


class DateInput(BaseInput[DefaultDate]):
    """Date input.

    Parameters
    ----------
    label : str
        Input label.
    default_input : DefaultDate
        Default value for the input.
    min_value : dt.date
        Minimum date.
    max_value : dt.date
        Maximum date.
    key : str
        Key for the date input.
    """

    def __init__(
        self,
        label: str,
        default_input: DefaultDate,
        min_value: dt.date,
        max_value: dt.date,
        key: str,
    ) -> None:
        super().__init__(label, default_input)
        self._min = min_value
        self._max = max_value
        self._key = key

    def build(self, container: "DeltaGenerator") -> "DateWidgetReturn":
        """Build the input in a given container.

        Parameters
        ----------
        container : DeltaGenerator
            Container to build the input object to.

        Returns
        -------
        DateWidgetReturn
            Input value.
        """
        return container.date_input(
            label=self.label,
            value=self._default.value,
            min_value=self._min,
            max_value=self._max,
            key=self._key,
        )


class PeriodInput:
    """Input Period.

    Parameters
    ----------
    label_min : str
        Label for the minimum date selector.
    label_max : str
        Label for the maximum date selector.
    min_date : dt.date
        Minimum possible date.
    max_date : dt.date
        Maximum Possible date.
    """

    def __init__(
        self,
        label_min: str,
        label_max: str,
        min_date: dt.date,
        max_date: dt.date,
        min_default: DefaultMinDate,
        max_default: DefaultMaxDate,
    ) -> None:
        self.label_min = label_min
        self.label_max = label_max
        self._min = min_date
        self._max = max_date
        self._min_default = min_default
        self._max_default = max_default

    def compute_min_end(
        self,
        min_chosen_date: "DateWidgetReturn",
    ) -> dt.date:
        """Compute minimum date for max date input.

        Parameters
        ----------
        min_chosen_date : DateWidgetReturn
            Date chosen in min date input.

        Returns
        -------
        dt.date
            Minimum chosen date if instance of date.
        """
        if isinstance(min_chosen_date, dt.date):
            return min_chosen_date
        return self._min

    def build(
        self,
        container: "DeltaGenerator",
    ) -> tuple["DateWidgetReturn", "DateWidgetReturn"]:
        """Build the input in a given container.

        Parameters
        ----------
        container : DeltaGenerator
            Container to build the input object to.

        Returns
        -------
        tuple["DateWidgetReturn", "DateWidgetReturn"]
            Minimum date, maximum date, to use as input values.
        """
        min_col, max_col = container.columns(2)

        min_input = DateInput(
            label=self.label_min,
            default_input=self._min_default,
            min_value=self._min,
            max_value=self._max,
            key="date_min_input",
        )
        min_chosen = min_input.build(min_col)

        max_input = DateInput(
            label=self.label_max,
            default_input=self._max_default,
            min_value=self.compute_min_end(min_chosen),
            max_value=self._max,
            key="date_max_input",
        )
        max_chosen = max_input.build(max_col)
        return min_chosen, max_chosen
