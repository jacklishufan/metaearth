"""Microsoft Planetary Computer (MPC) provider."""

import planetary_computer as pc
import pystac
from pystac_client import Client

from .base import STACProvider


class MicrosoftPlanetaryComputer(STACProvider):
    """Download data and extract assets from the Microsoft Planetary Computer."""

    _client: Client
    _description: str = "Microsoft Planetary Computer (MPC)"
    _default_client_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"

    # method override
    def asset_to_download_url(self, asset: pystac.Asset) -> str:
        """Sign the asset url with the MPC client and return URL."""
        return_url: str = pc.sign(asset.href)
        return return_url
