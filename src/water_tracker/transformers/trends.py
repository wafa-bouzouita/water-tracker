"""Compute trends to have some comparison basis."""
import datetime as dt

import numpy as np
import pandas as pd


class ExistingColumnNameError(Exception):
    """Wrong column name."""

    def __init__(self, column_name: str, *args: object) -> None:
        super().__init__(
            f"{column_name} already exists and would have been erased.",
            *args,
        )


class ThresholdError(Exception):
    """Not in any Threshold."""

    def __init__(self, *args: object) -> None:
        super().__init__(
            "The given trend does not fit in any of the provided thresholds.",
            *args,
        )


class TrendProperties:
    """Properties of the Average Trend.

    Parameters
    ----------
    measure_start : dt.date
        First date ofthe station's measures.
    measure_end : dt.date
        Last date of the station's measures.
    years_not_in_trend : int, optional
        Number of years to not use to compute the trend.
        For example, if measure_end is 2023/01/01,
        and years_not_in_trend equals 5,
        then no data after 2018/01/01 will be considered for the trend.
        , by default 5
    min_trend_length_year : int, optional
        Minimal number of year to use for the trend., by default 3
    """

    def __init__(
        self,
        measure_start: dt.date,
        measure_end: dt.date,
        years_not_in_trend: int = 5,
        min_trend_length_year: int = 3,
    ) -> None:
        self.years_not_in_trend = years_not_in_trend
        self.min_trend_length_year = min_trend_length_year
        self.has_enough_data = self._has_enough_data(
            measure_start=measure_start,
            measure_end=measure_end,
        )
        if not self.has_enough_data:
            self._start = None
            self._end = None
        else:
            self._start, self._end = self._get_trend_boundaries(
                measure_start=measure_start,
                measure_end=measure_end,
            )

    @property
    def trend_data_start(self) -> dt.date | None:
        """Starting date of the data to use for the trend.

        Returns
        -------
        dt.date | None
            Starting date of the data to use for the trend.
            None if there is not enough data to compute a trend.
        """
        return self._start

    @property
    def trend_data_end(self) -> dt.date | None:
        """Ending date of the data to use for the trend.

        Returns
        -------
        dt.date | None
            Ending date of the data to use for the trend.
            None if there is not enough data to compute a trend.
        """
        return self._end

    def _has_enough_data(
        self,
        measure_start: dt.date,
        measure_end: dt.date,
    ) -> bool:
        """Indicate if the stations has enough history to compute trend.

        Returns
        -------
        bool
            True if there's enough data to compute a trend.
        """
        measure_period = (measure_end - measure_start).days
        measure_years = measure_period / 365.25
        minimum_years_nb = self.years_not_in_trend + self.min_trend_length_year
        return measure_years >= minimum_years_nb

    @property
    def nb_years_history(self) -> int:
        """Number of year used for the trend.

        Returns
        -------
        float
            Number of years used for the trend.
        """
        if self._start is None or self._end is None:
            return 0
        return round((self._end - self._start).days / 365.25)

    def _get_trend_boundaries(
        self,
        measure_start: dt.date,
        measure_end: dt.date,
    ) -> tuple[dt.date, dt.date]:
        """Compute time boundaries for the trend data.

        Returns
        -------
        tuple[dt.date , dt.date ]
            First date for trend, last date for trend.
        """
        year_offset = pd.DateOffset(years=self.years_not_in_trend)
        ref_start_date = measure_start
        ref_end_date = (measure_end - year_offset).date()
        return ref_start_date, ref_end_date


class TrendThreshold:
    """Threshold to use to evaluate the relevancy of a Trend.

    Parameters
    ----------
    return_value : str
        Value to return if the threshold is satisfied.
    minimum_value : float
        Minimal value of the threshold (included).
    maximum_value : float
        Maximal value for the threshold (excluded).
    """

    def __init__(
        self,
        return_value: str,
        minimum_value: float,
        maximum_value: float,
    ) -> None:
        self.return_value = return_value
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value

    def verifies_minimum(self, value: float) -> bool:
        """Verify if a value is above the minimal value of the threshold.

        Parameters
        ----------
        value : float
            Value to test.

        Returns
        -------
        bool
            value >= threshold min
        """
        if np.isnan(self.minimum_value):
            return True
        return value >= self.minimum_value

    def verifies_maximum(self, value: float) -> bool:
        """Verify if a value is above the maximal value of the threshold.

        Parameters
        ----------
        value : float
            Value to test.

        Returns
        -------
        bool
            value < threshold max
        """
        if np.isnan(self.maximum_value):
            return True
        return value < self.maximum_value

    def is_in_threshold(self, trend: TrendProperties) -> bool:
        """Verify if a trend respects this threshold.

        Parameters
        ----------
        trend : TrendProperties
            The Trend to evaluate.

        Returns
        -------
        bool
            True if threshold min <= Trend years number < threshold max
        """
        years_history = trend.nb_years_history
        min_cond = self.verifies_minimum(years_history)
        max_cond = self.verifies_maximum(years_history)
        return min_cond and max_cond


class TrendEvaluation:
    """Trend Evaluation over given thresholds.

    Parameters
    ----------
    *thresholds : TrendThreshold
        Thresholds to consider in the evaluation.
    """

    def __init__(self, *thresholds: TrendThreshold) -> None:
        self.thresholds = thresholds

    def evaluate(self, trend: TrendProperties) -> str:
        """Evaluate a trend over all threshold.

        Parameters
        ----------
        trend : TrendProperties
            The Trend to evaluate.

        Returns
        -------
        str
            Return value of the first satisfied threshold.

        Raises
        ------
        ThresholdError
            If the Trend doesn't satisfy any of the thresholds.
        """
        for threshold in self.thresholds:
            if threshold.is_in_threshold(trend):
                return threshold.return_value
        raise ThresholdError


class AverageTrend:
    """Transform data to add historic averaged values as reference."""

    day_of_year_column: str = "day_of_year"
    mean_values_column: str = "mean_value"

    def add_days_of_year_column(
        self,
        dates_df: pd.DataFrame,
        dates_column: str,
        remove: bool = False,
    ) -> pd.DataFrame:
        """Add a 'day of year number' column to a DataFrame.

        Parameters
        ----------
        dates_df : pd.DataFrame
            DataFrame with regular dates in at least one column.
        dates_column : str
            Name of the column with dates values.
        remove : bool, optional
            Whether to remove the original date column or not.
            , by default False

        Returns
        -------
        pd.DataFrame
            Copy of dates_df with an additional column (named
            self.day_of_year_column) with the day of the year number.
            If 'remove' is True, the original dates column is removed.

        Raises
        ------
        ExistingColumnNameError
            If self.day_of_year_column is already the name of an existing
            column.
        """
        # get dates column
        if remove:
            dates = pd.to_datetime(dates_df.pop(dates_column))
        else:
            dates = pd.to_datetime(dates_df[dates_column])
        # transform to day of year (=> number between 1 and 366)
        days_of_year = dates.dt.day_of_year
        # add day of year column
        if self.day_of_year_column in dates_df.columns:
            raise ExistingColumnNameError(self.day_of_year_column)
        dates_df[self.day_of_year_column] = days_of_year
        return dates_df

    def compute_reference_values(
        self,
        history_days_of_year: pd.DataFrame,
        values_column: str,
    ) -> pd.DataFrame:
        """Compute the average value over the historic data.

        Parameters
        ----------
        history_days_of_year : pd.DataFrame
            DataFrame with the column self.day_of_year_column containing
            the day of year number.
        values_column : str
            Name of the column with the values to average.

        Returns
        -------
        pd.DataFrame
            DataFrame with the values averaged for each day of year.
        """
        # rename values_column
        values_column = history_days_of_year.pop(values_column)
        history_days_of_year[self.mean_values_column] = values_column
        # group by day
        day_group = history_days_of_year.groupby(self.day_of_year_column)
        # compute average value over the years
        return day_group.mean(numeric_only=True).reset_index()

    def transform(
        self,
        historical_df: pd.DataFrame,
        present_df: pd.DataFrame,
        dates_column: str,
        values_column: str,
    ) -> pd.DataFrame:
        """Add to present data the day-by-day average of 'value_column'.

        The average is computed over 'historical_df''s data. The joint is
        a left joint, performed over 'present_df'. Therefore, no data will be
        removed from 'present_df', but if 'historical_df' does not cover
        all days of a year, the average value will be 'np.nan'.

        Parameters
        ----------
        historical_df : pd.DataFrame
            DataFrame with historical values.
        present_df : pd.DataFrame
            DataFrame with present values.
        dates_column : str
            Name of the column containing date informations. Both
            'historical_df' and 'present_df' are supposed to have this column.
        values_column : str
            Name of the column containing the value to average. Both
            'historical_df' and 'present_df' are supposed to have this column.

        Returns
        -------
        pd.DataFrame
            Joint between present data and historical data average.
        """
        # Copy dataframes to avoid prevent modifications
        history_copy = historical_df[[dates_column, values_column]].copy()
        present_copy = present_df.copy()
        # replace date column by day of year
        history_days_of_year = self.add_days_of_year_column(
            dates_df=history_copy,
            dates_column=dates_column,
            remove=True,
        )
        present_day_of_year = self.add_days_of_year_column(
            dates_df=present_copy,
            dates_column=dates_column,
            remove=False,
        )
        # Compute reference values for historical data
        historical_reference = self.compute_reference_values(
            history_days_of_year=history_days_of_year,
            values_column=values_column,
        )
        # Joined averaged historical data to present data
        return present_day_of_year.merge(
            how="left",
            right=historical_reference,
            left_on=self.day_of_year_column,
            right_on=self.day_of_year_column,
        )
