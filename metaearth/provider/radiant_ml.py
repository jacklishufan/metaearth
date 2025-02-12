import json
import os

import dateutil.parser
from pystac_client.exceptions import APIError
from radiant_mlhub import Dataset

from metaearth.provider.base import STACProvider

from ..util.datetime import datetime_str_to_value

# Overwrite isoparse to handle the date format of LandCover Dataset
# TODO: Find a better way to handle this
# _old_parser = dateutil.parser.isoparse


def list_wrapper(f):
    """modify a function to consider f([arg]) and f(arg) as equivalent"""

    def g(*args, **kwargs):
        args = list(args)
        if isinstance(args[0], list):
            return f(args[0][0], *args[1:], **kwargs)
        return f(*args, **kwargs)

    return g


dateutil.parser.isoparse = list_wrapper(dateutil.parser.isoparse)

# import pystac_client after isoparse overwrite, overwrite flake8 checks
from pystac_client import Client  # noqa : E402


class RadiantMLHub(STACProvider):
    """Download data and extract assets from the Radient ML Hub."""

    _client: Client
    _description: str = "Radiant ML Hub (RADIANT)"
    _default_client_url: str = "https://api.radiant.earth/mlhub/v1"

    def __init__(self, client_url: str = "", api_key: str = "") -> None:
        """Set up the STAC client."""
        if client_url == "":
            client_url = self._default_client_url
        if api_key == "":
            api_key = os.environ.get("MLHUB_API_KEY")
        self.api_key = api_key
        self._client = Client.open(
            client_url, ignore_conformance=True, parameters={"key": api_key}
        )
        if not self.check_authorization():
            raise Exception(
                f"{self} is not authorized. See the documentation for {self}."
            )

    def check_authorization(self) -> bool:
        """Check if the provider is authorized."""
        try:
            self._client._stac_io.read_text("https://api.radiant.earth/mlhub/v1/search")
            return True
        except APIError:
            return False

    def download_dataset(
        self,
        dataset_id: str,
        output_dir: str,
        datetime_range_str: str,
        aoi_file: str,
        catalog_only=False,
    ):
        """Download a dataset to assigned output_dir"""
        all_datasets = [x.id for x in Dataset.list()]
        assert dataset_id in all_datasets, f"Dataset {dataset_id} does not exist"
        dataset = Dataset.fetch_by_id(dataset_id, api_key=self.api_key)
        with open(aoi_file) as f:
            aoi_data = json.loads(f.read())
            aoi = aoi_data["features"]
            assert len(aoi) == 1, "Radiant MLHub only supports one polygon filter"
            aoi = aoi[0]
        dataset.download(
            catalog_only=catalog_only,
            intersects=aoi,
            datetime=datetime_str_to_value(datetime_range_str),
            output_dir=output_dir,
            api_key=self.api_key,
        )
