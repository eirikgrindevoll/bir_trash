import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class TrashCollectionClient:
    """Client to interact with the Bir Trash API."""

    def __init__(self, app_id, contractor_id, request_timeout=10) -> None:
        """Initialize the client with the provided API token."""
        self.base_url = "https://webservice.bir.no/api"
        self.request_timeout = request_timeout
        self.app_id = app_id
        self.contractor_id = contractor_id
        self.token = None

    async def initialize(self):
        """Authenticate and retrieve token."""
        _LOGGER.info("Initializing client and attempting to authenticate")
        self.token = await self.authenticate()
        _LOGGER.info("Client initialized and authenticated successfully")

    async def authenticate(self):
        """Authenticate with the server and return the token."""
        async with aiohttp.ClientSession() as session:
            try:
                _LOGGER.info("Sending authentication request to the server")
                async with session.post(
                    f"{self.base_url}/login",
                    json={
                        "applikasjonsId": self.app_id,
                        "oppdragsgiverId": self.contractor_id,
                    },
                    timeout=self.request_timeout,
                ) as response:
                    response.raise_for_status()
                    token = response.headers["Token"]
                    _LOGGER.info(f"Authentication successful, received token: {token}")
                    return token
            except Exception as e:
                _LOGGER.error(f"Failed to authenticate: {e}")
                raise

    async def search_address(self, address):
        """Search for an address and return the corresponding ID."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/eiendommer",
                    params={"adresse": address},
                    headers={"Token": self.token},
                    timeout=self.request_timeout,
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    returnresult = result[0].get("id")
                    _LOGGER.info(f"Adresse ID  {returnresult} ")
                    return returnresult
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    _LOGGER.info("Token expired, refreshing token and retrying request")
                    self.token = await self.authenticate()
                    return await self.search_address(address)
                else:
                    raise

    async def get_calendar(self, address_id, fromdate, todate):
        """Get the calendar for the provided address ID."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/tomminger",
                    params={
                        "eiendomId": address_id,
                        "datoFra": fromdate,
                        "datoTil": todate,
                    },
                    headers={"Token": self.token},
                    timeout=self.request_timeout,
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    _LOGGER.info("Token expired, refreshing token and retrying request")
                    self.token = await self.authenticate()
                    return await self.get_calendar(address_id, fromdate, todate)
                else:
                    raise
