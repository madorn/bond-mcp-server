"""Bond Bridge API client for device communication."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BondAPIError(Exception):
    """Exception raised for Bond API errors."""
    pass


class BondClient:
    """Async client for Bond Bridge Local API."""
    
    def __init__(self, host: str, token: str, timeout: float = 10.0):
        """Initialize Bond client.
        
        Args:
            host: Bond Bridge IP address or hostname
            token: Bond API token
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.base_url = f"http://{self.host}/v2/"
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Bond-Token": self.token,  # Bond uses custom header
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Bond API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments for httpx request
            
        Returns:
            JSON response data
            
        Raises:
            BondAPIError: If API request fails
        """
        if not self._client:
            raise BondAPIError("Client not initialized. Use async context manager.")
        
        url = urljoin(self.base_url, endpoint)
        
        # Debug logging
        logger.debug(f"Making {method} request to: {url}")
        logger.debug(f"Headers: {self._client.headers}")
        
        try:
            response = await self._client.request(method, url, **kwargs)
            
            # Debug response
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return {"status": "success"}
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Bond API error {e.response.status_code}: {e.response.text}"
            logger.error(f"Full request details - URL: {url}, Headers: {self._client.headers}")
            logger.error(error_msg)
            raise BondAPIError(error_msg) from e
        except httpx.RequestError as e:
            error_msg = f"Bond API request failed: {str(e)}"
            logger.error(error_msg)
            raise BondAPIError(error_msg) from e
    
    async def get_bridge_info(self) -> Dict[str, Any]:
        """Get Bond Bridge information."""
        return await self._request("GET", "")
    
    async def list_devices(self) -> Dict[str, Any]:
        """List all devices connected to the Bond Bridge."""
        return await self._request("GET", "devices")
    
    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device information
        """
        return await self._request("GET", f"devices/{device_id}")
    
    async def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get current state of a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device state
        """
        return await self._request("GET", f"devices/{device_id}/state")
    
    async def send_action(self, device_id: str, action: str, argument: Optional[int] = None) -> Dict[str, Any]:
        """Send action to a device.
        
        Args:
            device_id: Device identifier
            action: Action to perform (e.g., "TurnOn", "TurnOff", "SetSpeed")
            argument: Optional argument for the action
            
        Returns:
            Action response
        """
        endpoint = f"devices/{device_id}/actions/{action}"
        data = {"argument": argument} if argument is not None else {}
        
        return await self._request("PUT", endpoint, json=data)
    
    # Convenience methods for common actions
    
    async def turn_on(self, device_id: str) -> Dict[str, Any]:
        """Turn on a device."""
        return await self.send_action(device_id, "TurnOn")
    
    async def turn_off(self, device_id: str) -> Dict[str, Any]:
        """Turn off a device."""
        return await self.send_action(device_id, "TurnOff")
    
    async def set_speed(self, device_id: str, speed: int) -> Dict[str, Any]:
        """Set fan speed (1-8, or 0 for off).
        
        Args:
            device_id: Fan device identifier
            speed: Speed level (0-8)
        """
        if speed == 0:
            return await self.turn_off(device_id)
        return await self.send_action(device_id, "SetSpeed", speed)
    
    async def set_direction(self, device_id: str, direction: int) -> Dict[str, Any]:
        """Set fan direction.
        
        Args:
            device_id: Fan device identifier
            direction: 1 for forward, -1 for reverse
        """
        return await self.send_action(device_id, "SetDirection", direction)
    
    async def open_shades(self, device_id: str) -> Dict[str, Any]:
        """Open shades completely."""
        return await self.send_action(device_id, "Open")
    
    async def close_shades(self, device_id: str) -> Dict[str, Any]:
        """Close shades completely."""
        return await self.send_action(device_id, "Close")
    
    async def set_position(self, device_id: str, position: int) -> Dict[str, Any]:
        """Set shade position.
        
        Args:
            device_id: Shade device identifier
            position: Position percentage (0-100)
        """
        return await self.send_action(device_id, "SetPosition", position)
    
    async def dim_light(self, device_id: str, brightness: int) -> Dict[str, Any]:
        """Set light brightness.
        
        Args:
            device_id: Light device identifier
            brightness: Brightness percentage (0-100)
        """
        return await self.send_action(device_id, "SetBrightness", brightness)