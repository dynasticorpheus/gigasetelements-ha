# gigasetelements-ha
A custom component for Home Assistant for Gigaset Elements Home Alarm.

Heavily based on the work of @nwiborg and @vlumikero.

The platform contains:
* Switch for arming Gigaset Elements Home Alarm in Away Mode
* Switch for arming Home mode
* Sensor to detect the status of the Home Alarm
* Alarm control panel that can be used with the corresponding Lovelace card

### Legal Disclaimer
This software is not affiliated with Gigaset and the developers take no legal responsibility for the functionality or security of your Gigaset Elements Alarm and devices.

# Installation

* Install repository through HACS

- OR -

* Create a "custom_components" folder where the configuration.yaml file is located, and sub folders equivalent to the structure in this repository.

* Update your configuration.yaml file according to the example file provided.
* Restart home assistant

# Example configuration.yaml

```yaml
gigasetelements:
    # Name for components
    name: "Gigaset Elements Alarm"
    # Username - your username to gigaset elements
    username: !secret gigasetelements_user
    # Password - your password to gigaset elements
    password: !secret gigasetelements_pw
``
