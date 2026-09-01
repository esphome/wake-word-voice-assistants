# ESPHome Wake Word Voice Assistants

This repo hosts YAML configurations for a curated selection of known, tested devices that can serve as wake word voice assistants for Home Assistant. The firmware built from these configurations can be installed from the [ESPHome projects page](https://esphome.io/projects/) with [esphome/esp-web-tools](https://github.com/esphome/esp-web-tools).

If a device is not included here it may have a suitable configuration in the [ESPHome Device Configuration Repository](https://devices.esphome.io/).

## Supported devices

| Device                                   | Configuration                            |
| ---------------------------------------- | ---------------------------------------- |
| ESP32 S3 Box                             | [esp32-s3-box](esp32-s3-box/)            |
| ESP32 S3 Box Lite                        | [esp32-s3-box-lite](esp32-s3-box-lite/)  |
| ESP32 S3 Box 3                           | [esp32-s3-box-3](esp32-s3-box-3/)        |
| M5Stack Atom Echo                        | [m5stack-atom-echo](m5stack-atom-echo/)  |

Each device directory contains the core config users adopt via the ESPHome dashboard import (`<device>.yaml`) and the factory wrapper built and published by CI (`<device>.factory.yaml`). The M5Stack Atom Echo additionally has a minimal factory configuration (`m5stack-atom-echo.minimal.factory.yaml`) whose binary is attached to each release.

The repository also holds shared assets used by the configurations: display images in [casita](casita/) and [error_box_illustrations](error_box_illustrations/), and audio files in [sounds](sounds/).
