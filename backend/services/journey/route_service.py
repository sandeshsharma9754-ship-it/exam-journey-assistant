from dataclasses import dataclass
from typing import Optional
import math
import urllib.parse
import urllib.request
import json


@dataclass
class RouteResult:
    distance_km: float
    duration_minutes: int
    source: str


class RouteServiceError(Exception):
    """Raised when route information cannot be obtained."""


class RouteService:
    """
    Provides route distance and estimated travel duration.

    The service currently uses the public OSRM routing service.
    The rest of the application only depends on RouteResult,
    so the routing provider can be replaced later without
    changing the journey/risk logic.
    """

    BASE_URL = "https://router.project-osrm.org"

    def get_route(
        self,
        starting_location: str,
        destination: str,
    ) -> RouteResult:

        if not starting_location.strip():
            raise RouteServiceError(
                "Starting location cannot be empty."
            )

        if not destination.strip():
            raise RouteServiceError(
                "Destination cannot be empty."
            )

        start_coordinates = self._geocode(starting_location)
        destination_coordinates = self._geocode(destination)

        if not start_coordinates:
            raise RouteServiceError(
                f"Could not find location: {starting_location}"
            )

        if not destination_coordinates:
            raise RouteServiceError(
                f"Could not find location: {destination}"
            )

        start_lon, start_lat = start_coordinates
        destination_lon, destination_lat = destination_coordinates

        route_url = (
            f"{self.BASE_URL}/route/v1/driving/"
            f"{start_lon},{start_lat};"
            f"{destination_lon},{destination_lat}"
            "?overview=false"
        )

        try:
            response = self._request_json(route_url)

            if response.get("code") != "Ok":
                raise RouteServiceError(
                    "Routing service could not calculate the route."
                )

            routes = response.get("routes", [])

            if not routes:
                raise RouteServiceError(
                    "No route was found between the locations."
                )

            route = routes[0]

            distance_km = route["distance"] / 1000
            duration_minutes = math.ceil(
                route["duration"] / 60
            )

            return RouteResult(
                distance_km=round(distance_km, 2),
                duration_minutes=duration_minutes,
                source="OSRM"
            )

        except RouteServiceError:
            raise

        except Exception as exc:
            raise RouteServiceError(
                f"Unable to retrieve route information: {exc}"
            ) from exc

    def _geocode(
        self,
        location: str
    ) -> Optional[tuple[float, float]]:

        encoded_location = urllib.parse.quote(location)

        url = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={encoded_location}"
            "&format=json"
            "&limit=1"
        )

        try:
            response = self._request_json(
                url,
                headers={
                    "User-Agent":
                        "ExamJourneyAssistant/1.0"
                }
            )

            if not response:
                return None

            result = response[0]

            latitude = float(result["lat"])
            longitude = float(result["lon"])

            return longitude, latitude

        except Exception as exc:
            raise RouteServiceError(
                f"Unable to locate '{location}': {exc}"
            ) from exc

    @staticmethod
    def _request_json(
        url: str,
        headers: Optional[dict] = None
    ):

        request = urllib.request.Request(
            url,
            headers=headers or {
                "User-Agent":
                    "ExamJourneyAssistant/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            return json.loads(
                response.read().decode("utf-8")
            )


def get_route(
    starting_location: str,
    destination: str
) -> RouteResult:
    """
    Convenience function for the rest of the application.
    """

    service = RouteService()

    return service.get_route(
        starting_location,
        destination
    )


if __name__ == "__main__":

    result = get_route(
        "Bhopal, Madhya Pradesh",
        "Indore, Madhya Pradesh"
    )

    print("Route Test")
    print("-" * 30)
    print(f"Distance : {result.distance_km} km")
    print(f"Duration : {result.duration_minutes} minutes")
    print(f"Source   : {result.source}")