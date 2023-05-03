"""Transformers for Meteo France data."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from water_tracker import BASE_DIR

depts_geojson_path_relative = Path("resources/departments_geojson.json")
depts_geojson_path = BASE_DIR.joinpath(depts_geojson_path_relative)


class SSWIMFTransformer:
    """Transformer to average SSWI values per department.

    Parameters
    ----------
    dryness_levels : list[str]
        List of all dryness levels to consider.
    """

    zone_column: str = "zone"
    geojson_columns_keep: dict[str, str] = {
        "code": zone_column,
        "geometry": "geometry",
    }
    dryness_levels_refs: dict[str, dict[str, float]] = {
        "extremely_moist": {"min": 1.75, "max": np.nan},
        "very_moist": {"min": 1.28, "max": 1.75},
        "moderately_moist": {"min": 0.84, "max": 1.28},
        "around_normal": {"min": -0.84, "max": 0.84},
        "moderately_dry": {"min": -1.28, "max": -0.84},
        "very_dry": {"min": -1.75, "max": -1.28},
        "extremely_dry": {"min": np.nan, "max": -1.75},
    }

    def __init__(self, dryness_levels: list[str]) -> None:
        refs = self.dryness_levels_refs
        mins = [refs[level]["min"] for level in dryness_levels]
        if np.nan in mins:
            self.min_level = np.nan
        else:
            self.min_level = min(mins)
        maxs = [refs[level]["max"] for level in dryness_levels]
        if np.nan in maxs:
            self.max_level = np.nan
        else:
            self.max_level = max(maxs)
        depts_geo: gpd.GeoDataFrame = gpd.read_file(depts_geojson_path)
        column_keep = self.geojson_columns_keep.keys()
        reindexed = depts_geo.reindex(columns=column_keep)
        self.depts_geo = reindexed.rename(columns=self.geojson_columns_keep)

    def join_dept_code(
        self,
        geographic_df: pd.DataFrame,
        latitude_column: str,
        longitude_column: str,
    ) -> pd.DataFrame:
        """Join an additional column with departments codes.

        Parameters
        ----------
        geographic_df : pd.DataFrame
            DataFrame to modify.
        latitude_column : str
            Name of the latitude column.
        longitude_column : str
            Name of the longitude column.

        Returns
        -------
        pd.DataFrame
            geographic_df with an additional column with department code.
        """
        longitude = geographic_df.pop(longitude_column)
        latitude = geographic_df.pop(latitude_column)
        geographic_df = gpd.GeoDataFrame(
            data=geographic_df,
            geometry=gpd.points_from_xy(x=longitude, y=latitude, crs=4326),
        )
        zones_df: gpd.GeoDataFrame = geographic_df.to_crs("EPSG:3395").sjoin(
            self.depts_geo.to_crs("EPSG:3395"),
            how="right",
        )
        return zones_df.drop(["index_left", "geometry"], axis=1)

    def compute_dryness_percentage(
        self,
        zones_df: pd.DataFrame,
        sswi_column: str,
    ) -> dict:
        """Compute the dryness percentage on each zone.

        Parameters
        ----------
        zones_df : pd.DataFrame
            DataFrame with the zones.
        sswi_column : str
            Name of the column with the sswi values.

        Returns
        -------
        dict
            Mapping between zone number and SSWI percentage.
        """
        if np.isnan(self.min_level):
            dryness_min = pd.Series(True, index=zones_df.index)
        else:
            dryness_min = zones_df[sswi_column] > self.min_level
        if np.isnan(self.max_level):
            dryness_max = pd.Series(True, index=zones_df.index)
        else:
            dryness_max = zones_df[sswi_column] <= self.max_level

        dryness_col = (dryness_min & dryness_max).astype(int)
        zones_df["values"] = dryness_col
        to_group = zones_df[[self.zone_column, "values"]]
        group_df = to_group.groupby(self.zone_column)
        averaged_percent = group_df.mean() * 100
        return averaged_percent["values"].to_dict()

    def transform(
        self,
        input_df: pd.DataFrame,
        latitude_col: str,
        longitude_col: str,
        sswi_col: str,
    ) -> pd.DataFrame:
        """Compute SSWI percentage per department.

        Parameters
        ----------
        input_df : pd.DataFrame
            Input dataframe.
        latitude_column : str
            Name of the latitude column.
        longitude_column : str
            Name of the longitude column.
        sswi_column : str
            Name of the column with the sswi values.

        Returns
        -------
        pd.DataFrame
            DataFrame with SSWI percentages.
        """
        geographic_df = input_df.copy()
        zones_df = self.join_dept_code(
            geographic_df=geographic_df,
            latitude_column=latitude_col,
            longitude_column=longitude_col,
        )
        return self.compute_dryness_percentage(
            zones_df=zones_df,
            sswi_column=sswi_col,
        )
