from datetime import datetime, timedelta
import logging
import pytz

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bir Trash sensors."""

    client = hass.data[DOMAIN][config_entry.entry_id]

    async def update_method():
        # Get today's date and the date 91 days from today, the pickup happends in Norway so forcing timezone
        oslo_tz = pytz.timezone("Europe/Oslo")
        oslo_now = datetime.now(oslo_tz)
        in_91_days = oslo_now + timedelta(days=91)
        fromdate = oslo_now.strftime("%Y-%m-%d")
        todate = in_91_days.strftime("%Y-%m-%d")

        # Fetch data from API and compute next pickup date for each fraksjon.
        data = await client.get_calendar(
            config_entry.data["address_id"], fromdate, todate
        )
        _LOGGER.debug(f"Received data from {fromdate} to {todate}: {data}")
        # Sort data by date
        data.sort(key=lambda item: item["dato"])
        # Compute next pickup date for each fraksjon
        next_pickup_dates = {}
        for item in data:
            if item["fraksjon"] not in next_pickup_dates:
                next_pickup_dates[item["fraksjon"]] = item["dato"]
        return next_pickup_dates

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=update_method,
        update_interval=timedelta(hours=1),
        request_refresh_debouncer=Debouncer(
            hass, _LOGGER, cooldown=60.0, immediate=True
        ),
    )
    _LOGGER.info(f"config_entry.data: {config_entry.data}")
    await coordinator.async_refresh()

    sensors = [
        BirTrashSensor(coordinator, config_entry, fraksjon)
        for fraksjon in coordinator.data
    ]

    async_add_entities(sensors)


class BirTrashSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Bir Trash sensor."""

    def __init__(self, coordinator, config_entry: ConfigEntry, fraksjon) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.fraksjon = fraksjon
        self.address = config_entry.data["address"]

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the sensor."""
        return f"bir_trash_{self.address}_{self.fraksjon}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"bir_trash_{self.address}_{self.fraksjon}"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        next_pickup_date = self.coordinator.data.get(self.fraksjon)
        if next_pickup_date:
            next_pickup_date = dt_util.parse_datetime(next_pickup_date)
            return next_pickup_date.isoformat()
        return None

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:trash-can-outline"
