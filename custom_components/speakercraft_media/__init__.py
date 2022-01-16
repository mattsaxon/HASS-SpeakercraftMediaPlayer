"""The speakercraft media player component."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'speakercraft_media'

class shareddata():
    pass

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    
    _LOGGER.debug("setup() entry")

    # Data that you want to share with your platforms
    hass.data[DOMAIN] = shareddata
    hass.data[DOMAIN].zones = None

    _LOGGER.debug("setup() exit")

    return True