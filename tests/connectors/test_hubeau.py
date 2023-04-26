"""Tests for hubeau connectors."""

from unittest.mock import Mock
from urllib.parse import urlsplit

import pandas as pd
import pytest
from pytest_mock import MockerFixture
from requests.exceptions import HTTPError
from water_tracker.connectors.hubeau import (
    HubeauConnector,
    PiezoChroniclesConnector,
    PiezoStationsConnector,
    retrieve_data_next_page,
)


@pytest.fixture()
def stations_connector() -> PiezoStationsConnector:
    """Instanciate a PiezoStationsConnector object.

    Returns
    -------
    PiezoStationsConnector
        Instanciated object.
    """
    return PiezoStationsConnector()


@pytest.fixture()
def chronicles_connector() -> PiezoChroniclesConnector:
    """Instanciate a PiezoChroniclesConnector object.

    Returns
    -------
    PiezoChroniclesConnector
        Instanciated object.
    """
    return PiezoChroniclesConnector()


def mock_stations_api_success(has_next: bool = False) -> Mock:
    """Generate mock response for a successful api call on stations.

    Parameters
    ----------
    has_next: bool
        Whether there is a next page or not.

    Returns
    -------
    Mock
        Mock successful response.
    """
    next_page = "next_page" if has_next else None
    response = Mock()
    response.json.return_value = {
        "count": 2,
        "first": "first_url",
        "last": None,
        "prev": None,
        "next": next_page,
        "api_version": "1.4.1",
        "data": [
            {
                "code_bss": "code1",
                "urn_bss": "urn_bss_value",
                "date_debut_mesure": "2022-01-01",
                "date_fin_mesure": "2023-01-01",
                "code_commune_insee": "code_commune1",
                "nom_commune": "nom_commune1",
                "x": 1,
                "y": 1,
                "codes_bdlisa": ["code11"],
                "urns_bdlisa": ["urns_bdlisa_value1"],
                "geometry": {},
                "bss_id": "id_bss1",
                "altitude_station": "-999.0",
                "nb_mesures_piezo": 100,
                "code_departement": "01",
                "nom_departement": "Ain",
                "libelle_pe": None,
                "profondeur_investigation": 1,
                "codes_masse_eau_edl": None,
                "noms_masse_eau_edl": None,
                "urns_masse_eau_edl": [],
                "date_maj": "Mon Nov 08 14:52:16 CET 2021",
            },
            {
                "code_bss": "code2",
                "urn_bss": "urn_bss_value",
                "date_debut_mesure": "2022-01-01",
                "date_fin_mesure": "2023-01-01",
                "code_commune_insee": "code_commune2",
                "nom_commune": "nom_commune2",
                "x": 1,
                "y": 1,
                "codes_bdlisa": ["code21"],
                "urns_bdlisa": ["urns_bdlisa_value2"],
                "geometry": {},
                "bss_id": "id_bss1",
                "altitude_station": "-999.0",
                "nb_mesures_piezo": 100,
                "code_departement": "01",
                "nom_departement": "Ain",
                "libelle_pe": None,
                "profondeur_investigation": 1,
                "codes_masse_eau_edl": None,
                "noms_masse_eau_edl": None,
                "urns_masse_eau_edl": [],
                "date_maj": "Mon Nov 08 14:52:16 CET 2021",
            },
        ],
    }
    response.status_code = 200
    response.raise_for_status.return_value = None
    return response


@pytest.fixture()
def stations_api_success_with_next() -> Mock:
    """Generate a mock response with a next page for stations API.

    Returns
    -------
    Mock
        Mocker.
    """
    return mock_stations_api_success(True)


@pytest.fixture()
def stations_api_success_without_next() -> Mock:
    """Generate a mock response without a next page for stations API.

    Returns
    -------
    Mock
        Mocker.
    """
    return mock_stations_api_success(False)


def mock_chronicles_api_success(has_next: bool = False) -> Mock:
    """Generate mock response for a successful api call on chronicles.

    Parameters
    ----------
    has_next: bool
        Whether there is a next page or not.

    Returns
    -------
    Mock
        Mock successful response.
    """
    next_page = "next_page" if has_next else None
    response = Mock()
    response.json.return_value = {
        "count": 2,
        "first": "url_first",
        "last": "url_last",
        "prev": None,
        "next": next_page,
        "api_version": "1.4.1",
        "data": [
            {
                "code_bss": "code_bss1",
                "urn_bss": "urn_bss1",
                "date_mesure": "2007-03-06",
                "timestamp_mesure": 1,
                "niveau_nappe_eau": 1,
                "mode_obtention": "str",
                "statut": "str",
                "qualification": "str",
                "code_continuite": "1",
                "nom_continuite": "str",
                "code_producteur": "1",
                "nom_producteur": "str",
                "code_nature_mesure": "str",
                "nom_nature_mesure": "str",
                "profondeur_nappe": 1,
            },
            {
                "code_bss": "code_bss2",
                "urn_bss": "urn_bss2",
                "date_mesure": "2007-03-07",
                "timestamp_mesure": 1,
                "niveau_nappe_eau": 1,
                "mode_obtention": "str",
                "statut": "str",
                "qualification": "str",
                "code_continuite": "2",
                "nom_continuite": "str",
                "code_producteur": "1",
                "nom_producteur": "str",
                "code_nature_mesure": "N",
                "nom_nature_mesure": "str",
                "profondeur_nappe": 1,
            },
        ],
    }
    response.status_code = 200
    response.raise_for_status.return_value = None
    return response


@pytest.fixture()
def chronicles_api_success_with_next() -> Mock:
    """Generate a mock response with a next page for chronicles API.

    Returns
    -------
    Mock
        Mocker.
    """
    return mock_chronicles_api_success(True)


@pytest.fixture()
def chronicles_api_success_without_next() -> Mock:
    """Generate a mock response with a next page for chronicles API.

    Returns
    -------
    Mock
        Mocker.
    """
    return mock_chronicles_api_success(False)


@pytest.fixture()
def mock_api_fail() -> Mock:
    """Generate mock response for a failed api call.

    Parameters
    ----------
    mocker : MockerFixture
        Mocker fixture.

    Returns
    -------
    Mock
        Mock failed response.
    """
    response = Mock()
    response.json.return_value = {}
    response.status_code = 400
    response.raise_for_status.side_effect = HTTPError("Connexion refused.")
    response.raise_for_status.return_value = None
    return response


@pytest.mark.parametrize(
    "connector_fixture",
    ["stations_connector", "chronicles_connector"],
)
def test_hubeau_connector_url(
    connector_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    """Assert url to call has a valid fomat.

    Ensure that the url has a scheme, and a valid netloc.

    Parameters
    ----------
    connector_fixture : str
        Name of the fixture.
    request : pytest.FixtureRequest
        A request for a fixture from a test or fixture function.
    """
    connector: PiezoStationsConnector = request.getfixturevalue(
        connector_fixture,
    )
    parsed_url = urlsplit(connector.url)
    assert parsed_url.scheme
    assert parsed_url.netloc == "hubeau.eaufrance.fr"


@pytest.mark.parametrize(
    ("connector_fixture", "response"),
    [
        ("stations_connector", "stations_api_success_without_next"),
        ("chronicles_connector", "chronicles_api_success_without_next"),
    ],
)
def test_connector_retrieve_success(
    connector_fixture: str,
    response: str,
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
) -> None:
    """Test hubeau connectors for a successful api response.

    Parameters
    ----------
    connector_fixture : str
        Name of the connector fixture.
    response : str
        Name of the successful mocked api response.
    request : pytest.FixtureRequest
        Request for a fixture.
    mocker: MockerFixture
        Mocker for patching.
    """
    connector: HubeauConnector = request.getfixturevalue(connector_fixture)
    mocker_response: Mock = request.getfixturevalue(response)
    mocker.patch("requests.get", return_value=mocker_response)
    params: dict = {}
    output_df = connector.retrieve(params)
    columns_keep = connector.columns_to_keep
    date_cols = connector.date_columns
    assert not output_df.empty
    assert all((col in columns_keep) for col in output_df.columns)
    assert all(output_df.dtypes[col] == "datetime64[ns]" for col in date_cols)


@pytest.mark.parametrize(
    "connector_fixture",
    ["stations_connector", "chronicles_connector"],
)
def test_connector_retrieve_fail(
    connector_fixture: str,
    mock_api_fail: Mock,
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
) -> None:
    """Test hubeau connectors for a failed api response.

    Parameters
    ----------
    connector_fixture : str
        Name of the connector fixture.
    mock_api_fail : Mock
        Mocked failed API request.
    request : pytest.FixtureRequest
        Request for a fixture.
    mocker: MockerFixture
        Mocker for patching.
    """
    connector: HubeauConnector = request.getfixturevalue(connector_fixture)
    mocker.patch("requests.get", return_value=mock_api_fail)
    params: dict = {}
    output_df = connector.retrieve(params)
    assert output_df.empty


@pytest.mark.parametrize(
    "response",
    [
        "chronicles_api_success_without_next",
        "stations_api_success_without_next",
    ],
)
def test_retrieve_success_without_next(
    response: str,
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
) -> None:
    """Test retrieve_data_next_page when there's no next page.

    Parameters
    ----------
    response : str
        Name of the API response fixture.
    mocker : MockerFixture
        Mocker for patching.
    request : pytest.FixtureRequest
        Request for a fixture.
    """
    api_response: Mock = request.getfixturevalue(response)
    mocker.patch("requests.get", return_value=api_response)
    url = "https://example.com/"
    params: dict = {}
    output_df, next_page = retrieve_data_next_page(url=url, params=params)
    assert not next_page
    assert output_df.equals(pd.DataFrame(api_response.json()["data"]))


@pytest.mark.parametrize(
    "response",
    [
        "chronicles_api_success_with_next",
        "stations_api_success_with_next",
    ],
)
def test_retrieve_success_with_next(
    response: str,
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
) -> None:
    """Test retrieve_data_next_page when there is a next page.

    Parameters
    ----------
    response : str
        Name of the API response fixture.
    mocker : MockerFixture
        Mocker for patching.
    request : pytest.FixtureRequest
        Request for a fixture.
    """
    api_response: Mock = request.getfixturevalue(response)
    mocker.patch("requests.get", return_value=api_response)
    url = "https://example.com/"
    params: dict = {}
    output_df, next_page = retrieve_data_next_page(url=url, params=params)
    assert next_page == api_response.json()["next"]
    assert output_df.equals(pd.DataFrame(api_response.json()["data"]))


def test_retrieve_fail(
    mock_api_fail: Mock,
    mocker: MockerFixture,
) -> None:
    """Test retrieve_data_next_page when the api call fails.

    Parameters
    ----------
    response : str
        Name of the API response fixture.
    mocker : MockerFixture
        Mocker for patching.
    request : pytest.FixtureRequest
        Request for a fixture.
    """
    mocker.patch("requests.get", return_value=mock_api_fail)
    url = "https://example.com/"
    params: dict = {}
    output_df, next_page = retrieve_data_next_page(url=url, params=params)
    assert not next_page
    assert output_df.empty
