# Gigaset Elements - Custom Component for Home-Assisant

This project is a custom component for [Home-Assistant](https://home-assistant.io) providing [Gigaset Smart Home](https://www.gigaset.com/hq_en/smart-home/) integration.


## Installation

### Via HACS

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

### Manually
1. Copy the files from the `custom_component/gigasetelements/` folder into the `custom_component/gigasetelements/` of your Home-Assistant installation.

### Common Steps
1. Configure the sensors following the instructions in `Configuration`.
2. Restart the Home-Assitant instance.


## Configuration

### Schema
```yaml
- platform: gigasetelements
  name:
  username:
  password:
  scan_interval:
```

### Parameters
* `name`: Name of the sensor (e.g. gigaset_elements).
* `username`: Gigaset Elements username. [https://app.gigaset-elements.com](https://app.gigaset-elements.com/)   
* `password`: Gigaset Elements password.
* `scan_interval`: (Optional) Set how many seconds should pass in between refreshes. Don't set this to low to avoid issues.

### Example
```yaml
- platform: gigasetelements
  name: gigaset_elements
  username: !secret gigasetelements_username
  password: !secret gigasetelements_password
  scan_interval: 60
```
## Credits
Initial release based on the excellent [Securitas](https://github.com/vlumikero/home-assistant-securitas) custom component.

## Donation Hall of Fame
If you like this custom component you might want to consider to [BuyMeABeer? 🍺](https://buymeacoffee.com/dynasticorpheus)
