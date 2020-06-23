# Gigaset Elements - Custom Component for Home-Assisant
[![Total alerts](https://img.shields.io/lgtm/alerts/g/dynasticorpheus/gigasetelements-ha.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/dynasticorpheus/gigasetelements-ha/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/dynasticorpheus/gigasetelements-ha.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/dynasticorpheus/gigasetelements-ha/context:python)
[![Downloads for latest release](https://img.shields.io/github/downloads/dynasticorpheus/gigasetelements-ha/latest/total.svg)](https://github.com/dynasticorpheus/gigasetelements-ha/releases/latest)

This project is a custom component for [Home-Assistant](https://home-assistant.io) providing [Gigaset Smart Home](https://www.gigaset.com/hq_en/smart-home/) integration.

![Install](https://asset.conrad.com/media10/isa/160267/c1/-/nl/1650392_BB_00_FB/image.jpg)

## Installation

### Via HACS

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

### Manually
1. Copy the files from the `custom_component/gigasetelements/` folder into the `custom_component/gigasetelements/` of your Home-Assistant installation.

### Common Steps
1. Configure the sensors following the instructions in `Configuration`.
2. Restart the Home-Assitant instance.


## Configuration

### Schema
```yaml
gigasetelements:
  name:
  username:
  password:
```

### Parameters
* `name`: Name of the sensor (e.g. gigaset_elements).
* `username`: Gigaset Elements username. [https://app.gigaset-elements.com](https://app.gigaset-elements.com/)   
* `password`: Gigaset Elements password.

### Example
```yaml
gigasetelements:
  name: gigaset_elements
  username: !secret gigasetelements_username
  password: !secret gigasetelements_password
```

## Current integrations
* Alarm Control Panel
* Sensor (state, health, door, window, smoke)
* Switch (away, night, custom)
* Smart Plug

## Credits
Initial release based on the excellent [Securitas](https://github.com/vlumikero/home-assistant-securitas) custom component.

## Donation Hall of Fame
If you like this custom component you might want to consider to [BuyMeABeer? 🍺](https://buymeacoffee.com/dynasticorpheus)
