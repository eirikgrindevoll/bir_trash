"""The Bir Trash integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .trash_collection_client import TrashCollectionClient

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bir Trash from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Create API instance
    app_id = "94FA72AD-583D-4AA3-988F-491F694DFB7B"
    contractor_id = "100;300;400"
    client = TrashCollectionClient(app_id, contractor_id)
    await client.initialize()

    # Store an API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
