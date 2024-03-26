# Gigaset Elements - Custom Component for Home-Assisant - DISCONTINUED after 2024-Mar-29
[![Github stars](https://img.shields.io/github/stars/dynasticorpheus/gigasetelements-ha.svg)](https://github.com/dynasticorpheus/gigasetelements-ha/stargazers/)
[![Github forks](https://img.shields.io/github/forks/dynasticorpheus/gigasetelements-ha.svg)](https://github.com/dynasticorpheus/gigasetelements-ha/network/members/)
[![CodeQL](https://github.com/dynasticorpheus/gigasetelements-ha/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/dynasticorpheus/gigasetelements-ha/actions/workflows/codeql-analysis.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dynasticorpheus_gigasetelements-ha&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dynasticorpheus_gigasetelements-ha)
[![BuyMeCoffee](https://camo.githubusercontent.com/cd005dca0ef55d7725912ec03a936d3a7c8de5b5/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6275792532306d6525323061253230636f666665652d646f6e6174652d79656c6c6f772e737667)](https://buymeacoffee.com/dynasticorpheus)

This project is a custom component for [Home-Assistant](https://home-assistant.io) providing [Gigaset Smart Home](https://www.gigaset.com/hq_en/smart-home/) integration.

**End of service warning: [Gigaset has announced to terminate operations for the Gigaset Home Cloud at 2024-Mar-29](https://www.gigaset.com/hq_en/cms/smart-home-overview.html).**

**As this integration uses the Gigaset API endpoints, you can expect it to no longer work after that.**

<img src="https://asset.conrad.com/media10/isa/160267/c1/-/nl/1650392_BB_00_FB/image.jpg" width="75%">

## Installation

### Via HACS

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

### Manually
1. Copy the files from the `custom_component/gigasetelements/` folder into the `custom_component/gigasetelements/` of your Home-Assistant installation.

### Common Steps
1. Configure the sensors following the instructions in `Configuration`.
2. Restart the Home-Assitant instance.


## Configuration (*configuration.yaml*)

### Schema
```yaml
gigasetelements:
  name:
  username:
  password:
  switches:
  code:
  code_arm_required:
```

### Parameters
* `name`: Name of the sensor (e.g. gigaset_elements).
* `username`: Gigaset Elements username. [https://app.gigaset-elements.com](https://app.gigaset-elements.com/)   
* `password`: Gigaset Elements password.
* `switches`: True or False (Optional)
* `code`: Code to enable or disable the alarm in the frontend. (Optional)
* `code_arm_required`: True or False (Optional)

### Example
```yaml
gigasetelements:
  name: gigaset_elements
  username: !secret gigasetelements_username
  password: !secret gigasetelements_password
  switches: True
  code: 1234
  code_arm_required: False
```

## Current integrations
* Alarm Control Panel (code)
* Binary Sensor (door, window, smoke, motion, camera_motion, universal, button, siren)
* Sensor (base, climate, thermostat)
* Switch (away, custom, night, panic, plug, privacy)

## Alarm mode mapping
| Gigaset Elements | Home Assistant |
| ---------------- | -------------- |
| home             | disarmed       |
| custom           | arm_home       |
| away             | arm_away       |
| night            | arm_night      |

## Credits
Initial release based on the excellent [Securitas](https://github.com/vlumikero/home-assistant-securitas) custom component.

## Donation Hall of Fame
If you like this custom component you might want to consider to [BuyMeABeer? 🍺](https://buymeacoffee.com/dynasticorpheus)

* *Orkun S*
* *Adrian R*
* *Joshua T*
* *Auke C*
* *RPC B*
* *Silke H*
* *Frank M*
* *Max G*
* *Andreas G*
* *Florian B*
