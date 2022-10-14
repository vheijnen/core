"""Tests for the Jellyfin media_player platform."""
from unittest.mock import MagicMock

from aiohttp import ClientSession

from homeassistant.components.jellyfin.const import DOMAIN
from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    STATE_IDLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry


async def test_media_player(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
) -> None:
    """Test the Jellyfin media player."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    state = hass.states.get("media_player.jellyfin_device")

    assert state
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "JELLYFIN-DEVICE"
    assert state.attributes.get(ATTR_ICON) is None
    assert state.state == STATE_IDLE

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry.device_id
    assert entry.entity_category is None
    assert entry.unique_id == "SERVER-UUID-SESSION-UUID"

    device = device_registry.async_get(entry.device_id)
    assert device
    assert device.configuration_url is None
    assert device.connections == set()
    assert device.entry_type is None
    assert device.hw_version is None
    assert device.identifiers == {(DOMAIN, "DEVICE-UUID")}
    assert device.manufacturer == "Jellyfin"
    assert device.name == "JELLYFIN-DEVICE"
    assert device.sw_version == "1.0.0"


async def test_browse_media(
    hass: HomeAssistant,
    hass_ws_client: ClientSession,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
) -> None:
    """Test Jellyfin browse media."""
    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expected_child_item = {
        "title": "COLLECTION FOLDER",
        "media_class": MediaClass.DIRECTORY.value,
        "media_content_type": "collection",
        "media_content_id": "COLLECTION-FOLDER-UUID",
        "can_play": False,
        "can_expand": True,
        "thumbnail": "http://localhost/Items/COLLECTION-FOLDER-UUID/Images/Primary.jpg",
        "children_media_class": None,
    }

    assert response["result"]["media_content_id"] == ""
    assert response["result"]["media_content_type"] == "root"
    assert response["result"]["title"] == "Jellyfin"
    assert response["result"]["children"][0] == expected_child_item

    await client.send_json(
        {
            "id": 2,
            "type": "media_player/browse_media",
            "entity_id": "media_player.jellyfin_device",
            "media_content_type": "collection",
            "media_content_id": "COLLECTION-FOLDER-UUID",
        }
    )

    response = await client.receive_json()
    expected_child_item = {
        "title": "EPISODE",
        "media_class": MediaClass.EPISODE.value,
        "media_content_type": MediaType.EPISODE.value,
        "media_content_id": "EPISODE-UUID",
        "can_play": True,
        "can_expand": False,
        "thumbnail": "http://localhost/Items/EPISODE-UUID/Images/Primary.jpg",
        "children_media_class": None,
    }

    assert response["success"]
    assert response["result"]["media_content_id"] == "COLLECTION-FOLDER-UUID"
    assert response["result"]["title"] == "FOLDER"
    assert response["result"]["children"][0] == expected_child_item
