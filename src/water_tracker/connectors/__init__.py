"""Connectors to retrieve data from providers."""


from water_tracker.connectors.copernicus import PrecipitationsERA5Connector
from water_tracker.connectors.hubeau import (
    PiezoChroniclesConnector,
    PiezoStationsConnector,
)
from water_tracker.connectors.meteo_france import (
    PrecipitationsMFConnector,
    SSWIMFConnector,
)

__all__ = [
    "PiezoChroniclesConnector",
    "PiezoStationsConnector",
    "PrecipitationsERA5Connector",
    "SSWIMFConnector",
    "PrecipitationsMFConnector",
]
