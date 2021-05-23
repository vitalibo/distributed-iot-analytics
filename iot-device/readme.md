# IoT Device :: Arduino Uno

Device communicate with digital temperature sensor that measures temperature and relative humidity and publish changes
to Device Gateway over Ethernet protocol.

### Schematics

![breadboard](https://raw.githubusercontent.com/vitalibo/distributed-iot-analytics/assets/iot-device/ArduinoUno_Breadboard.png)

### Components

- [Arduino Uno](https://store.arduino.cc/arduino-uno-rev3)
- [Ethernet Shield](https://www.arduino.cc/en/Main/ArduinoEthernetShieldV1)
- [DHT11 Humidity / Temperature Sensor Module](https://www.itead.cc/wiki/DHT11_Humidity_Temperature_Sensor_Brick)
- Jumper wires (generic)

### Specifications

| Name | Value |
|---|---|
| Temperature range | 0 to 50 ºC +/-2 ºC |
| Humidity range | 20 to 90% +/-5% |
| Connection speed | 10/100Mb |
| Operating Voltage | 5V |
| Microcontroller | ATmega328P |
| Flash Memory | 32 KB |
| SRAM | 2 KB |
| Frequency | 16 MHz |

## Usage

Before start, you need install `arduino-cli`, follow
this [instruction](https://arduino.github.io/arduino-cli/latest/installation/) to do that.

To install the arduino:avr platform core, run the following:

```shell
arduino-cli core install arduino:avr
```

To compile the sketch you run the compile command, passing the proper FQBN string:

```shell
arduino-cli compile --fqbn arduino:avr:uno --libraries src/arduino/libraries/ --output-dir target/ src/arduino/sketch/
```

To upload the sketch to your board, run the following command, using the serial port your board is connected to:

```shell
arduino-cli upload --fqbn arduino:avr:uno --port /dev/cu.usbserial-14620 -i target/sketch.ino.hex
```
