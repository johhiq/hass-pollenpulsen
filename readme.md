# Pollenpulsen Integration for Home Assistant

This custom integration provides pollen forecasts for Swedish regions using data from the Palynological Laboratory at the Swedish Museum of Natural History.

## Features

- Real-time pollen forecasts for all Swedish regions
- Detailed national forecast with pollen distribution maps
- Individual sensors for each pollen type
- Configurable update intervals
- Supports both regional and national forecasts
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

The integration can be configured entirely through the UI. You can:

1. Select your region (e.g., Stockholm, Borlänge, Sverige)
2. Choose which pollen types to monitor
3. Set the update interval (1-24 hours, default: 3 hours)

## Entities

The integration creates two types of entities:

### Forecast Sensor
- Shows the current state of the forecast ("active", "no_data", or "unavailable")
- Includes structured attributes with forecast text, period, region, and detailed pollen levels
- Provides a comprehensive overview of all pollen types in the region

### Pollen Level Sensors
- Individual sensors for each selected pollen type
- Shows current pollen levels (0-8)
- Includes description of the level (Inga halter, Låga, Måttliga, Höga, Mycket höga, Extremt höga, Data saknas, Pollensäsongen ej börjat, Pollensäsongen är slut)

## Attributes

### Forecast Sensor Attributes
- `last_updated`: Timestamp of the last data update
- `forecast`: Object containing:
  - `text`: Complete forecast text
  - `start_date`: Start date of the current forecast
  - `end_date`: End date of the current forecast
  - `region`: Region name
- `pollen_levels`: Array of pollen information objects, each containing:
  - `type`: Pollen type name
  - `type_id`: Pollen type ID
  - `level`: Current level (0-8)
  - `description`: Text description of the level
- `metadata`: Object containing:
  - `attribution`: Data source attribution
  - `last_update_success`: Whether the last update was successful

### Pollen Level Sensor Attributes
- `type`: Pollen type name
- `type_id`: Pollen type ID
- `region`: Region name
- `forecast_period`: Object containing:
  - `start`: Start date of the forecast
  - `end`: End date of the forecast
- `description`: Text description of the current level

## Data Source

Data is provided by the Palynological Laboratory at the Swedish Museum of Natural History through their official API.

## Contributing

Feel free to submit issues and pull requests.

## License

[MIT License](LICENSE)
