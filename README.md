# Creality Assistant (HACS Integration)

**Creality Assistant** is a custom Home Assistant integration available via HACS that connects to your Creality K2 Plus 3D printer over a WebSocket connection. It dynamically creates and updates sensor entities based on data received from the printer. **Please note:** This integration is in early development and is currently only being tested on the Creality K2. It is recommended not to use it in production environments.

## Features

- **Real-Time Data:**  
  Continuously receives JSON data from the printer and updates sensors dynamically.

- **Dynamic Sensors:**  
  For each key received from the printer, a Home Assistant sensor is created and updated automatically.

- **Connection Status:**  
  Includes a dedicated connection status sensor that displays the current connection state (e.g., CONNECTED, ERROR).

- **Config Flow:**  
  Setup and configuration are handled through Home Assistant's web UI. Configure IP address, port (default is 9999), and an optional password.

- **Debug Logging:**  
  Extensive debug logging is enabled to help track the integration's operations and troubleshoot issues.

## Installation

1. **HACS Installation:**
   - Add this integration via HACS by including the repository URL.
   - Once installed, the `creality_assistant` folder (containing `__init__.py`, `manifest.json`, `config_flow.py`, `const.py`, `sensor.py`, and `websocket_client.py`) will be placed in your `custom_components` directory.
   - Restart Home Assistant.

2. **Manual Installation:**
   - Clone or download the repository and place the folder in your `custom_components` directory.
   - Restart Home Assistant.

## Configuration

After installation, add the integration via the Home Assistant UI:

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **Creality Assistant**.
3. Enter the following information:
   - **IP Address:** The IP address of your printer.
   - **Port:** The port the printer uses for WebSocket communication (default is 9999).
   - **Password:** (Optional) If your printer requires a password.
4. Complete the setup.

## Debugging

Enable debug logging for the integration to see detailed logs. For example, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.creality_assistant: debug
