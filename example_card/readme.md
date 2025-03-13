# Pollenpulsen Example Card

This is an example card configuration for displaying pollen forecasts in Home Assistant using the Pollenpulsen integration.

## Prerequisites

This card requires the following custom cards to be installed:
- [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)

You can install Mushroom Cards via HACS (Home Assistant Community Store).

## Installation

1. Copy the content of `example_card.yaml` to your dashboard
2. Replace `stockholm` in `sensor.pollenprognos_stockholm` with your configured region
3. Make sure you have the Mushroom Cards installed


## Features

- Displays current pollen forecast text and period
- Shows individual cards for each pollen type
- Color-coded indicators based on pollen levels:
  - Green: No pollen (level 0)
  - Yellow: Low levels (level 1-2)
  - Orange: Moderate levels (level 3-4)
  - Red: High levels (level 5)
  - Grey: No data/Season information (level 6-8)

## Customization

To use the card with a different region, replace all instances of `stockholm` in the YAML with your region name. For example, for Göteborg:

```yaml
sensor.pollenprognos_goteborg
```

## Support

Please note that this is just an example card configuration. It is provided as-is without any guarantee of updates or maintenance. Feel free to use it as a starting point and modify it to suit your needs.

If you have issues with the Pollenpulsen integration itself, please refer to the main repository.

