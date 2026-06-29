# OpenNextion ONX2432G028

This directory contains the ESPHome wake-word voice assistant configuration for the OpenNextion ONX2432G028 board.

## Adaptation status

The ONX2432G028 adaptation is functionally complete for the wake-word voice assistant use case.

- ESP32-S3R8, 16 MB flash, and 8 MB OPI PSRAM are configured.
- ST7789 display output is working with 240×320 resolution and BGR color order.
- CST826 touch input is mapped for the current landscape UI.
- PDM microphone input is working on GPIO19/GPIO20.
- I2S speaker output is working on GPIO16/GPIO14/GPIO15 with the amplifier enabled through PCF8574 EXIO0.
- Wi-Fi placement matters for TTS streaming reliability; keep the board near a stable 2.4 GHz AP and watch for ESPHome `Roam scan` log messages if audio playback becomes delayed or choppy.

## Hardware summary

| Function | Configuration |
| :--- | :--- |
| MCU | ESP32-S3R8 |
| Flash | 16 MB |
| PSRAM | 8 MB OPI PSRAM |
| LCD | 2.8" ST7789 SPI TFT, 240×320 |
| LCD color order | BGR |
| Touch | CST826 on I2C address `0x15` |
| IO expander | PCF8574 on I2C address `0x38` |
| Microphone | PDM microphone |
| Speaker | I2S speaker with PCF8574-controlled amplifier |

## Pin map

Only pins used by the current ESPHome voice assistant configuration are listed here.

| Function | Pin |
| :--- | :--- |
| I2C SCL | GPIO7 |
| I2C SDA | GPIO8 |
| LCD SCLK | GPIO5 |
| LCD MOSI | GPIO1 |
| LCD CS | GPIO2 |
| LCD DC | GPIO3 |
| LCD BL | GPIO6 |
| LCD RST | PCF8574 EXIO6 |
| Touch | I2C polling on address `0x15` |
| PDM MIC CLK | GPIO19 |
| PDM MIC DATA | GPIO20 |
| Speaker I2S LRCLK | GPIO16 |
| Speaker I2S BCLK | GPIO14 |
| Speaker I2S SDIN | GPIO15 |
| Speaker CTRL | PCF8574 EXIO0 |

## Verified hardware

- The ST7789 display initializes and covers the expected 240×320 physical area.
- The UI is visible in landscape orientation with display `rotation: 90`.
- The BGR color order is correct for this panel.
- The CST826 touch controller reports usable coordinates through I2C address `0x15`.
- The PDM microphone captures voice for Home Assistant Assist.
- The I2S speaker plays Home Assistant TTS responses.
- Home Assistant Assist timers can ring on the device and be stopped by touching the screen.

## Configurations

| File | Purpose |
| :--- | :--- |
| `onx2432g028.yaml` | Wake-word voice assistant configuration adapted from `esp32-s3-box-3` |

## Home Assistant setup

After flashing, first connect the device to Wi-Fi. Once it is online, Home Assistant connects to it through the ESPHome native API.

### Wi-Fi provisioning

The ONX2432G028 configuration enables ESPHome's fallback access point and captive portal. If the device cannot connect to a known Wi-Fi network after boot, it starts its own temporary Wi-Fi access point.

1. Power on the flashed ONX2432G028 board.
2. Wait for the fallback ESPHome access point to appear in your phone or computer Wi-Fi list. For example, it may look like `onx2432g028-a1b2c3`, where the suffix is generated from the device MAC address.
3. Connect to the fallback access point for this device.
4. Open the captive portal page if it does not open automatically: `http://192.168.4.1/`.
5. Select your 2.4 GHz Wi-Fi network and enter the password.
6. Wait for the board to reboot or reconnect to the configured Wi-Fi.
7. Continue with Home Assistant discovery or add the ESPHome integration manually.

Use a stable 2.4 GHz network for voice assistant use. Weak signal or roaming scans can delay TTS streaming and make playback choppy.

For the official ESPHome captive portal and Home Assistant getting started flow, see:

```text
https://esphome.io/components/captive_portal/
https://esphome.io/guides/getting_started_hassio/
```

### Home Assistant discovery

If Home Assistant discovers the device automatically:

1. Open Home Assistant.
2. Go to **Settings > Devices & services**.
3. Find the discovered ESPHome device and select **Configure**.
4. Follow the on-screen setup flow.

If it is not discovered automatically:

1. Go to **Settings > Devices & services**.
2. Select **Add integration**.
3. Choose **ESPHome**.
4. Enter the device hostname or IP address and the native API port, usually `6053`.

For the official ESPHome integration flow, see the Home Assistant ESPHome integration documentation:

```text
https://www.home-assistant.io/integrations/esphome/
```

### Assist voice pipeline

To use this board as a voice assistant, configure Home Assistant Assist and select the desired pipeline for speech-to-text, intent handling, and text-to-speech. The upstream voice assistant documentation is here:

```text
https://www.home-assistant.io/voice_control/
```

The ONX2432G028 YAML exposes a speaker media player and microphone to the ESPHome voice assistant component, so Home Assistant can use it as an Assist satellite once the ESPHome device is added.

When an Assist timer finishes, the board plays the timer alarm sound. Touch the screen while the alarm is ringing to stop it.

## Local validation

If your shell is in the repository root, validate the source YAML with:

```bash
esphome config OpenNextion/ONX2432G028/onx2432g028.yaml
```

If your shell is elsewhere, pass the path to `onx2432g028.yaml` from your current directory, or use an absolute path.

## Device Builder sync

ESPHome Device Builder shows device cards for YAML files placed directly in its configuration root. Keep the source file in this repository under `OpenNextion/ONX2432G028/`, but copy the main YAML file itself to the Device Builder root:

```bash
cp OpenNextion/ONX2432G028/onx2432g028.yaml /path/to/esphome/config/onx2432g028.yaml
```

Do not copy the whole `OpenNextion/ONX2432G028/` directory into the ESPHome configuration directory. Command-line ESPHome can compile nested YAML paths, but the Device Builder web UI will not show a device card unless the YAML file is in the configuration root.

Only sync the main YAML file and resources directly required by that YAML file, such as images, audio, fonts, or packages. Do not sync documentation or local working notes into the Device Builder configuration directory.

To compile:

```bash
esphome compile OpenNextion/ONX2432G028/onx2432g028.yaml
```

To flash and view logs, replace the serial device if needed:

```bash
esphome run OpenNextion/ONX2432G028/onx2432g028.yaml --device /dev/ttyUSB0
```
