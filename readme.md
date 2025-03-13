# Pollenpulsen Integration for Home Assistant

This custom integration provides pollen forecasts for Swedish regions using data from the Palynological Laboratory at the Swedish Museum of Natural History.

## Features

- Real-time pollen forecasts for all Swedish regions
- Comprehensive forecast data including all pollen types
- Configurable update interval
- Available in Swedish and English

## Installation

### Manual Installation

1. Copy the `custom_components/pollenpulsen` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings -> Devices & Services
4. Click "Add Integration"
5. Search for "Pollenpulsen"
6. Follow the configuration steps

## Configuration

The integration can be configured through the UI:

1. Select your region (e.g., Stockholm, Borlänge, Sverige)
2. Set the update interval (1-24 hours, default: 3 hours) - applies to all configured regions

## Entities

The integration creates one sensor entity per configured region:

### Forecast Sensor (`sensor.pollenprognos_<region>`)
- Shows the current state of the forecast ("active", "no_data", or "unavailable")
- Includes comprehensive attributes with forecast data and pollen levels

### Attributes

The forecast sensor provides the following attributes:

- `last_updated`: Timestamp of the last data update
- `forecast`: Object containing:
  - `text`: Complete forecast text
  - `start_date`: Start date of the current forecast
  - `end_date`: End date of the current forecast
  - `region`: Region name
- `pollen_levels`: Array of pollen information objects, each containing:
  - `type`: Pollen type name (e.g., "Al", "Björk", "Gräs")
  - `type_id`: Pollen type ID
  - `level`: Current level (0-8)
  - `description`: Text description of the level
- `metadata`: Object containing:
  - `attribution`: Data source attribution
  - `last_update_success`: Whether the last update was successful

## Example Values

### Pollen Levels
- 0: Inga halter
- 1: Låga halter
- 2: Låga till måttliga halter
- 3: Måttliga halter
- 4: Måttliga till höga halter
- 5: Höga halter
- 6: Data saknas
- 7: Pollensäsongen ej börjat
- 8: Pollensäsongen är slut

## Template Examples

To get the pollen level for a specific type (e.g., Björk in Stockholm):
```yaml
{{ state_attr('sensor.pollenprognos_stockholm', 'pollen_levels') | selectattr('type', 'eq', 'Björk') | list | first | attr('level') }}
```

To get the description for a specific pollen type:
```yaml
{{ state_attr('sensor.pollenprognos_stockholm', 'pollen_levels') | selectattr('type', 'eq', 'Björk') | list | first | attr('description') }}
```

## Example Dashboard Card

An example card configuration is provided in the `example_card` directory. This card uses Mushroom Cards to display:
- Current pollen forecast
- Individual cards for each pollen type
- Color-coded indicators based on pollen levels

To use the example card:
1. Install [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) via HACS
2. Check the `example_card/readme.md` for installation instructions

## Data Source

Data is provided by the Palynological Laboratory at the Swedish Museum of Natural History through their official API.

## Contributing

Feel free to submit issues and pull requests.

## License

[MIT License](LICENSE)
