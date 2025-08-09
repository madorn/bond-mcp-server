"""FastMCP server for Bond Bridge device control."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import fastmcp
from fastmcp import FastMCP

from .bond_client import BondClient, BondAPIError
from .config import get_config, validate_config
from .models import (
    ActionRequest,
    ActionType,
    DeviceInfo,
    DeviceListResponse,
    DeviceState,
    DeviceType,
    ErrorResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global configuration and client
config = validate_config()
mcp = FastMCP(config.server_name)


async def get_bond_client() -> BondClient:
    """Get configured Bond client."""
    return BondClient(
        host=config.bond_host,
        token=config.bond_token,
        timeout=config.timeout
    )


@mcp.tool()
async def list_devices() -> Dict[str, Any]:
    """List all Bond devices connected to the bridge.
    
    Returns:
        Dictionary containing all devices with their basic information.
    """
    try:
        async with await get_bond_client() as client:
            devices_data = await client.list_devices()
            
            # Transform the data for better readability
            devices = {}
            for device_id, device_info in devices_data.items():
                if not device_id.startswith('_'):  # Skip metadata
                    devices[device_id] = {
                        "id": device_id,
                        "name": device_info.get("name", "Unknown"),
                        "type": device_info.get("type", "Unknown"),
                        "location": device_info.get("location", "")
                    }
            
            return {
                "devices": devices,
                "total_count": len(devices)
            }
    except BondAPIError as e:
        return {"error": f"Failed to list devices: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error listing devices: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_device_info(device_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific device.
    
    Args:
        device_id: The Bond device identifier
        
    Returns:
        Detailed device information including capabilities and properties.
    """
    try:
        async with await get_bond_client() as client:
            device_info = await client.get_device_info(device_id)
            return {
                "device_id": device_id,
                "info": device_info
            }
    except BondAPIError as e:
        return {"error": f"Failed to get device info: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error getting device info: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_device_state(device_id: str) -> Dict[str, Any]:
    """Get current state of a Bond device.
    
    Args:
        device_id: The Bond device identifier
        
    Returns:
        Current device state including power, speed, direction, etc.
    """
    try:
        async with await get_bond_client() as client:
            state = await client.get_device_state(device_id)
            return {
                "device_id": device_id,
                "state": state
            }
    except BondAPIError as e:
        return {"error": f"Failed to get device state: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error getting device state: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def toggle_device_power(device_id: str) -> Dict[str, Any]:
    """Toggle power state of a Bond device (on/off).
    
    Args:
        device_id: The Bond device identifier
        
    Returns:
        Result of the toggle operation.
    """
    try:
        async with await get_bond_client() as client:
            # Get current state to determine action
            current_state = await client.get_device_state(device_id)
            power = current_state.get("power", 0)
            
            if power == 1:
                result = await client.turn_off(device_id)
                action = "turned off"
            else:
                result = await client.turn_on(device_id)
                action = "turned on"
            
            return {
                "device_id": device_id,
                "action": action,
                "result": result
            }
    except BondAPIError as e:
        return {"error": f"Failed to toggle device power: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error toggling device power: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def set_fan_speed(device_id: str, speed: int) -> Dict[str, Any]:
    """Set fan speed for a ceiling fan device.
    
    Args:
        device_id: The Bond fan device identifier
        speed: Fan speed level (0-8, where 0 is off)
        
    Returns:
        Result of the speed change operation.
    """
    if not (0 <= speed <= 8):
        return {"error": "Fan speed must be between 0 and 8"}
    
    try:
        async with await get_bond_client() as client:
            result = await client.set_speed(device_id, speed)
            return {
                "device_id": device_id,
                "speed": speed,
                "action": "off" if speed == 0 else f"set to speed {speed}",
                "result": result
            }
    except BondAPIError as e:
        return {"error": f"Failed to set fan speed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error setting fan speed: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def set_fan_direction(device_id: str, direction: str) -> Dict[str, Any]:
    """Set fan direction for a ceiling fan device.
    
    Args:
        device_id: The Bond fan device identifier
        direction: Fan direction ("forward" or "reverse")
        
    Returns:
        Result of the direction change operation.
    """
    direction_map = {"forward": 1, "reverse": -1}
    
    if direction.lower() not in direction_map:
        return {"error": "Direction must be 'forward' or 'reverse'"}
    
    try:
        async with await get_bond_client() as client:
            dir_value = direction_map[direction.lower()]
            result = await client.set_direction(device_id, dir_value)
            return {
                "device_id": device_id,
                "direction": direction.lower(),
                "result": result
            }
    except BondAPIError as e:
        return {"error": f"Failed to set fan direction: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error setting fan direction: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def control_shades(device_id: str, action: str, position: Optional[int] = None) -> Dict[str, Any]:
    """Control motorized shades.
    
    Args:
        device_id: The Bond shade device identifier
        action: Action to perform ("open", "close", or "set_position")
        position: Position percentage (0-100) when action is "set_position"
        
    Returns:
        Result of the shade control operation.
    """
    valid_actions = ["open", "close", "set_position"]
    if action.lower() not in valid_actions:
        return {"error": f"Action must be one of: {', '.join(valid_actions)}"}
    
    if action.lower() == "set_position" and (position is None or not (0 <= position <= 100)):
        return {"error": "Position must be between 0 and 100 when setting position"}
    
    try:
        async with await get_bond_client() as client:
            if action.lower() == "open":
                result = await client.open_shades(device_id)
            elif action.lower() == "close":
                result = await client.close_shades(device_id)
            else:  # set_position
                result = await client.set_position(device_id, position)
            
            return {
                "device_id": device_id,
                "action": action.lower(),
                "position": position if action.lower() == "set_position" else None,
                "result": result
            }
    except BondAPIError as e:
        return {"error": f"Failed to control shades: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error controlling shades: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def set_light_brightness(device_id: str, brightness: int) -> Dict[str, Any]:
    """Set brightness for a dimmable light device.
    
    Args:
        device_id: The Bond light device identifier
        brightness: Brightness percentage (0-100, where 0 is off)
        
    Returns:
        Result of the brightness change operation.
    """
    if not (0 <= brightness <= 100):
        return {"error": "Brightness must be between 0 and 100"}
    
    try:
        async with await get_bond_client() as client:
            if brightness == 0:
                result = await client.turn_off(device_id)
                action = "turned off"
            else:
                result = await client.dim_light(device_id, brightness)
                action = f"set to {brightness}% brightness"
            
            return {
                "device_id": device_id,
                "brightness": brightness,
                "action": action,
                "result": result
            }
    except BondAPIError as e:
        return {"error": f"Failed to set light brightness: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error setting light brightness: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def send_custom_action(device_id: str, action: str, argument: Optional[int] = None) -> Dict[str, Any]:
    """Send a custom action to a Bond device.
    
    Args:
        device_id: The Bond device identifier
        action: Bond action name (e.g., "TurnOn", "TurnOff", "SetSpeed")
        argument: Optional argument for the action
        
    Returns:
        Result of the custom action.
    """
    try:
        async with await get_bond_client() as client:
            result = await client.send_action(device_id, action, argument)
            return {
                "device_id": device_id,
                "action": action,
                "argument": argument,
                "result": result
            }
    except BondAPIError as e:
        return {"error": f"Failed to send custom action: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error sending custom action: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_bridge_info() -> Dict[str, Any]:
    """Get Bond Bridge information and status.
    
    Returns:
        Bridge information including version, uptime, and configuration.
    """
    try:
        async with await get_bond_client() as client:
            bridge_info = await client.get_bridge_info()
            return {
                "bridge": bridge_info,
                "server_config": {
                    "host": config.bond_host,
                    "timeout": config.timeout,
                    "max_retries": config.max_retries
                }
            }
    except BondAPIError as e:
        return {"error": f"Failed to get bridge info: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error getting bridge info: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def main():
    """Main entry point for the Bond MCP server."""
    logger.info(f"Starting Bond MCP Server v{config.server_version}")
    logger.info(f"Connecting to Bond Bridge at {config.bond_host}")
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, config.log_level))
    
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()