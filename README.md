# Bond MCP Server

A Model Context Protocol (MCP) server that provides tools for controlling [Bond Bridge](https://bondhome.io/product/bond-bridge/) smart home devices. This server enables AI assistants like Claude to interact with ceiling fans, fireplaces, shades, lights, and other RF-controlled devices through Bond Bridge hubs.

## Features

- **Device Management**: List and get information about all connected Bond devices
- **Fan Control**: Control ceiling fan speed, direction, and power state
- **Shade Control**: Open, close, and set positions for motorized shades
- **Light Control**: Control dimmable lights and brightness levels
- **Custom Actions**: Send any Bond API action to devices
- **Bridge Information**: Get Bond Bridge status and configuration

## Quick Start

### Prerequisites

- Bond Bridge on your local network
- Bond API token (obtained from Bond Home app)

### Getting Your Bond Token

1. Open the Bond Home app on your mobile device
2. Go to Settings → Bond Bridge → Advanced → API
3. Copy the Local Token (not the Cloud Token)

### Add to your MCP settings:

```json
{
  "mcpServers": {
    "bond": {
      "command": "podman",
      "args": [
        "run", "-i", "--rm",
        "-e", "BOND_TOKEN=your_token_here",
        "-e", "BOND_HOST=192.168.1.100",
        "quay.io/madorn/bond-mcp-server:latest"
      ]
    }
  }
}
```

## Installation

1. **Create and activate virtual environment:**
   ```bash
   python3.11 -m venv bond-mcp-env
   source bond-mcp-env/bin/activate  # On Windows: bond-mcp-env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Bond Bridge settings
   ```

4. **Run the server:**
   ```bash
   python -m bond_mcp.server
   ```

### Configuration

Create a `.env` file with your Bond Bridge configuration:

```env
# Required: Bond Bridge settings
BOND_TOKEN=your_bond_api_token_here
BOND_HOST=192.168.1.100

# Optional: Connection settings
BOND_TIMEOUT=10.0
BOND_MAX_RETRIES=3
BOND_RETRY_DELAY=1.0

# Optional: Logging
LOG_LEVEL=INFO
```

## Available Tools

### Device Management
- `list_devices()` - List all Bond devices
- `get_device_info(device_id)` - Get detailed device information
- `get_device_state(device_id)` - Get current device state
- `get_bridge_info()` - Get Bond Bridge information

### Device Control
- `toggle_device_power(device_id)` - Toggle device on/off
- `send_custom_action(device_id, action, argument?)` - Send custom Bond action

### Fan Control
- `set_fan_speed(device_id, speed)` - Set fan speed (0-8)
- `set_fan_direction(device_id, direction)` - Set direction ("forward"/"reverse")

### Shade Control
- `control_shades(device_id, action, position?)` - Control shades
  - Actions: "open", "close", "set_position"
  - Position: 0-100 (for set_position action)

### Light Control
- `set_light_brightness(device_id, brightness)` - Set brightness (0-100)

### Bond API Reference

This server uses the Bond Local API v2:
- Base URL: `http://{bridge_ip}/v2/`
- Authentication: Bearer token in Authorization header
- Docs: [Bond Local API Documentation](https://docs-local.appbond.com)

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure Bond Bridge IP is correct and accessible
2. **Authentication failed**: Verify Bond token is correct (use Local Token, not Cloud Token)
3. **Device not found**: Check device ID exists using `list_devices()`
4. **Action not supported**: Verify device supports the action using `get_device_info()`

### Debug Logging

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your environment.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
