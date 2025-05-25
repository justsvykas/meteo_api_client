import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from pytz import timezone

from meteo_api import LOGGER


class MeteoClient:
    """Client for accessing weather forecast and observation data from the Meteo.lt API.

    This class provides methods to retrieve weather forecasts, historical observations,
    and metadata about places and weather stations from the public Meteo.lt API.

    Attributes:
        BASE_URL (str): The base URL for the Meteo.lt API.
        TIME_ZONE (timezone): Default timezone for timestamp data (Europe/Vilnius).

    Methods:
        get_place_forecast_by_type: Get forecast data for a specific place
        get_station_historical_observations: Get historical data for a specific date
        get_station_historical_observations_range: Fetch data over a date range.

    Exploratory methods:
        get_places: Get a list of available places for forecasts.
        get_place_info: Get detailed information about a specific place.
        get_place_forecasts: Get available forecast types for a specific place.
        get_stations: Get a list of weather stations.
        get_station_info: Get information about a specific weather station.
        get_more_station_info: Get stored observation data for a weather station.
    """

    BASE_URL = "https://api.meteo.lt/v1"
    TIME_ZONE = timezone("Europe/Vilnius")

    def __init__(self, session: requests.Session = None) -> None:
        """Initialize the MeteoClient."""
        self.session = session or requests.Session()

    def get_place_forecast_by_type(
        self,
        place_code: str,
        forecast_type: str = "long-term",
        time_zone: timezone = TIME_ZONE,
    ) -> pd.DataFrame:
        """Returns the weather forecast data for a place."""
        response = self.session.get(
            f"{self.BASE_URL}/places/{place_code}/forecasts/{forecast_type}"
        )
        response.raise_for_status()
        return self._json_to_dataframe(
            response.json(), record_path="forecastTimestamps", time_zone=time_zone
        )

    def get_station_historical_observations(
        self, station_code: str, date: str = "latest", time_zone: timezone = TIME_ZONE
    ) -> pd.DataFrame:
        """Returns stored observation data from a specific station at specific time."""
        response = self.session.get(
            f"{self.BASE_URL}/stations/{station_code}/observations/{date}"
        )
        response.raise_for_status()
        return self._json_to_dataframe(
            response.json(), record_path="observations", time_zone=time_zone
        )

    def get_station_historical_observations_range(
        self,
        station_code: str,
        start_date: datetime,
        end_date: datetime,
        time_zone: timezone = TIME_ZONE,
    ) -> pd.DataFrame:
        """Fetch observations from a specified start date to an end date."""
        all_dfs = []
        current_date = start_date.date()

        while current_date <= end_date.date():
            LOGGER.info(f"Fetching data for {current_date}...")

            try:
                df_observations = self.get_station_historical_observations(
                    station_code, date=current_date.isoformat(), time_zone=time_zone
                )
                if not df_observations.empty:
                    all_dfs.append(df_observations)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # noqa: PLR2004
                    LOGGER.warning("Hit rate limit (429). Sleeping for 5 seconds...")
                    time.sleep(5)
                    continue
                raise

            time.sleep(0.15)
            current_date += timedelta(days=1)

        return pd.concat(all_dfs) if all_dfs else pd.DataFrame()

    def get_places(self) -> pd.DataFrame:
        """Returns a list of places available for weather forecasts."""
        response = self.session.get(f"{self.BASE_URL}/places")
        response.raise_for_status()
        return self._json_to_dataframe(response.json())

    def get_place_info(self, place_code: str) -> pd.DataFrame:
        """Returns detailed information about a specific place."""
        response = self.session.get(f"{self.BASE_URL}/places/{place_code}")
        response.raise_for_status()
        return self._json_to_dataframe(response.json())

    def get_place_forecasts(self, place_code: str) -> pd.DataFrame:
        """Returns the list of forecast types available for a specific place."""
        response = self.session.get(f"{self.BASE_URL}/places/{place_code}/forecasts")
        response.raise_for_status()
        return self._json_to_dataframe(response.json())

    def get_stations(self) -> pd.DataFrame:
        """Returns a list of weather stations with observation data."""
        response = self.session.get(f"{self.BASE_URL}/stations")
        response.raise_for_status()
        return self._json_to_dataframe(response.json())

    def get_station_info(self, station_code: str) -> pd.DataFrame:
        """Returns information about a specific weather station."""
        response = self.session.get(f"{self.BASE_URL}/stations/{station_code}")
        response.raise_for_status()
        return self._json_to_dataframe(response.json())

    def get_more_station_info(self, station_code: str) -> pd.DataFrame:
        """Returns stored observation data from a specific station."""
        response = self.session.get(
            f"{self.BASE_URL}/stations/{station_code}/observations"
        )
        response.raise_for_status()
        return self._json_to_dataframe(response.json())

    def _find_record_path(
        self, data: dict, record_path: str | None = None
    ) -> str | None:
        """Find record path.

        If record_path is provided and valid, use that e.g. "observations".
        Otherwise, pick the first key whose value is a non-empty list of dicts.
        """
        if record_path and record_path in data:
            val = data[record_path]
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return record_path

        for key, val in data.items():
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return key

        return None

    def _flatten_meta(self, data: dict, record_path: str) -> dict:
        """Take top-level keys except record_path and flatten to meta_{key}_{subkey}."""
        flat_meta = {}
        for key, val in data.items():
            if key == record_path:
                continue
            if isinstance(val, dict):
                for subk, subv in val.items():
                    flat_meta[f"{key}_{subk}"] = subv
            else:
                flat_meta[key] = val
        return flat_meta

    def _set_timestamp_index(
        self, df: pd.DataFrame, time_zone: timezone = TIME_ZONE
    ) -> pd.DataFrame:
        """Converts timestamp columns to time-zone aware datetime index."""
        time_columns = [col for col in df.columns if col.endswith("TimeUtc")]

        if not time_columns:
            LOGGER.warning("No column ending with 'TimeUtc' found in DataFrame.")
            return df

        for col in time_columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].dt.tz_localize("UTC", ambiguous="infer")
            if time_zone:
                df[col] = df[col].dt.tz_convert(time_zone)
        return df.set_index(time_columns[0]).rename_axis("timestamp").sort_index()

    def _json_to_dataframe(
        self,
        json_data: dict | list,
        record_path: str | None = None,
        time_zone: timezone = TIME_ZONE,
    ) -> pd.DataFrame:
        """Convert JSON data to a pandas DataFrame."""
        if isinstance(json_data, list):
            return pd.DataFrame(json_data)

        if isinstance(json_data, dict):
            rp = self._find_record_path(json_data, record_path)
            if rp:
                records = json_data[rp]
                meta = self._flatten_meta(json_data, rp)
                df_records_and_meta = pd.json_normalize(
                    data={**meta, rp: records}, record_path=rp, meta=list(meta.keys())
                )
                return self._set_timestamp_index(df_records_and_meta, time_zone)

            return pd.DataFrame([json_data])
        return pd.DataFrame()
