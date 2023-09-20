"""Config flow for Bir Trash integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .trash_collection_client import TrashCollectionClient

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("address"): str,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    # Use your app_id and contractor_id
    app_id = "94FA72AD-583D-4AA3-988F-491F694DFB7B"
    contractor_id = "100;300;400"
    client = TrashCollectionClient(app_id, contractor_id)
    try:
        _LOGGER.info("Initializing the client and authenticating")
        await client.initialize()
    except Exception as e:
        _LOGGER.error(f"Failed to authenticate: {e}")
        raise CannotConnect from e

    # Attempt to get properties for the provided address
    try:
        address_id = await client.search_address(data["address"])
    except Exception as e:
        _LOGGER.error(f"Failed to search address: {e}")
        raise CannotConnect from e

    # Log the return info
    _LOGGER.info(
        f"Returning config entry: Trash Collection ({data['address']}), address_id: {address_id}"
    )
    # Return info that you want to store in the config entry.
    return {"title": f"Trash Collection ({data['address']})", "address_id": address_id}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bir Trash."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                #
                # return self.async_create_entry(title=info["title"], data=user_input)

                return self.async_create_entry(
                    title=info["title"],
                    data={**user_input, "address_id": info["address_id"]},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
