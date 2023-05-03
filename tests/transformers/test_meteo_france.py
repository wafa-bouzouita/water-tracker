"""Tests for Meteo France Transformers."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from pytest_mock import MockerFixture
from shapely import Polygon
from water_tracker.transformers.meteo_france import SSWIMFTransformer


@pytest.fixture()
def transformer(mocker: MockerFixture) -> SSWIMFTransformer:
    """SSWI Transformer.

    Parameters
    ----------
    mocker : MockerFixture
        Mocker fixture.

    Returns
    -------
    SSWIMFTransformer
        SSWI Transformer.
    """
    mocker.patch("water_tracker.transformers.meteo_france.gpd.read_file")
    SSWIMFTransformer.dryness_levels_refs = {
        "value1": {"min": np.nan, "max": 1},
        "value2": {"min": 1, "max": 2},
        "value3": {"min": 2, "max": np.nan},
    }
    transformer = SSWIMFTransformer(["value1", "value2"])
    transformer.depts_geo = gpd.GeoDataFrame(
        {"zone": ["01", "10", "30"]},
        geometry=[
            Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
            Polygon([[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]),
            Polygon([[3, 3], [4, 3], [4, 4], [3, 4], [3, 3]]),
        ],
        index=[0, 1, 2],
        crs=4326,
    )
    return transformer


@pytest.mark.parametrize(
    ("dryness_levels", "expected_min", "expected_max"),
    [
        (["value1", "value2"], np.nan, 2),
        (["value1"], np.nan, 1),
        (["value3"], 2, np.nan),
        (["value1", "value3"], np.nan, np.nan),
    ],
)
def test_transformer_init_dryness_levels_minmax_values(
    dryness_levels: list[str],
    expected_max: float,
    expected_min: float,
    mocker: MockerFixture,
) -> None:
    """Test the transformer min and max values.

    Parameters
    ----------
    mocker : MockerFixture
        Mocker Fixture.
    """
    SSWIMFTransformer.dryness_levels_refs = {
        "value1": {"min": np.nan, "max": 1},
        "value2": {"min": 1, "max": 2},
        "value3": {"min": 2, "max": np.nan},
    }
    mocker.patch("water_tracker.transformers.meteo_france.gpd.read_file")
    transformer = SSWIMFTransformer(dryness_levels)
    if np.isnan(expected_max):
        assert np.isnan(transformer.max_level)
    else:
        assert transformer.max_level == expected_max
    if np.isnan(expected_min):
        assert np.isnan(transformer.min_level)
    else:
        assert transformer.min_level == expected_min


def test_join_dept_code(
    transformer: SSWIMFTransformer,
) -> None:
    """Test the satial join between Points and zone Polygons.

    Parameters
    ----------
    transformer : SSWIMFTransformer
        SSWI Transformer.
    """
    input_df = pd.DataFrame(
        {
            "value": [1, 2, 3],
            "latitude": [0.1, 2.0, 8],
            "longitude": [0.5, 1.5, 6.2],
        },
    )
    expected_df = pd.DataFrame(
        {
            "value": [1, 2, np.nan],
            "zone": ["01", "10", "30"],
        },
        index=[0, 1, 2],
    )
    output_df = transformer.join_dept_code(
        input_df,
        "latitude",
        "longitude",
    )
    assert output_df.equals(expected_df)


@pytest.mark.parametrize(
    ("min_level", "max_level", "expected_value"),
    [
        (np.nan, 1, {"01": 50.0, "15": 0.0, "12": 100.0}),
        (3, np.nan, {"01": 50.0, "15": 0.0, "12": 0.0}),
        (np.nan, np.nan, {"01": 100.0, "15": 100.0, "12": 100.0}),
        (1, 2, {"01": 0.0, "15": 50.0, "12": 0.0}),
        (2, 1, {"01": 0.0, "15": 0.0, "12": 0.0}),
    ],
)
def test_compute_dryness_percentage_min_nan(
    transformer: SSWIMFTransformer,
    min_level: float,
    max_level: float,
    expected_value: dict[str, float],
) -> None:
    """Test the dryness percentage computation.

    Parameters
    ----------
    transformer : SSWIMFTransformer
        SSWI Transformer.
    min_level : float
        Minimum level value for the transformer.
    max_level : float
        Maximum level value for the transformer.
    expected_value : dict[str, float]
        Expected output.
    """
    zones_df = pd.DataFrame(
        {
            "value": [1, 5, 3, 2, -10],
            "zone": ["01", "01", "15", "15", "12"],
        },
        index=[0, 1, 2, 3, 4],
    )
    transformer.min_level = min_level
    transformer.max_level = max_level
    output_dict = transformer.compute_dryness_percentage(
        zones_df=zones_df,
        sswi_column="value",
    )
    assert output_dict == expected_value


@pytest.mark.parametrize(
    ("min_level", "max_level", "expected_value"),
    [
        (1.5, 2, {"01": 50.0, "10": 100.0, "30": 0.0}),
        (np.nan, 2, {"01": 100.0, "10": 100.0, "30": 0.0}),
    ],
)
def test_transform(
    transformer: SSWIMFTransformer,
    min_level: float,
    max_level: float,
    expected_value: dict[str, float],
) -> None:
    """Test the complete transformation pipeline.

    Parameters
    ----------
    transformer : SSWIMFTransformer
        SSWI Transformer.
    """
    transformer.min_level = min_level
    transformer.max_level = max_level
    input_df = pd.DataFrame(
        {
            "value": [1, 1.6, 2, 3],
            "latitude": [0.1, 0.11, 2.0, 8],
            "longitude": [0.5, 0.6, 1.5, 6.2],
        },
    )
    output_dict = transformer.transform(
        input_df=input_df,
        latitude_col="latitude",
        longitude_col="longitude",
        sswi_col="value",
    )
    assert output_dict == expected_value
