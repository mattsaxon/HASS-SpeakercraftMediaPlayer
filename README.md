# HASS-SpeakercraftMediaPlayer
Speakercraft MZC Platform for Home Assistant

Repository created for install via [HACS](https://hacs.xyz/docs/setup/download) based on code by [@sjeffrey101](https://github.com/sjeffrey101) [here](https://github.com/sjeffrey101/homeassistant_speakercraft/tree/main/old%20ha%20component/custom_components/speakercraft_media)

Example Configuration.yaml

```
media_player:
      - platform: speakercraft_media
        zones: 
          1: "Lounge Speakers"
          2: "Kitchen Speakers"
          3: "Den Speakers"
          4: "Outside Speakers"
          5: "Master Speakers"
          6: "bed1 Speakers"
          7: "bed2 Speakers"
          8: "Bathroom Speakers"
        serial_port: "/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0"
        sources:
          3: "Sr3"
          4: "Sr4"
          5: "Alexa"
        default_volume: 20
        default_source: 5
        power_target: switch.speakercraft
```
