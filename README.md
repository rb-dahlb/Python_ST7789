# Python_ST7789
Python library for using ST7789-based IPS LCD with Raspberry Pi.

Forked from [solinnovay/Python_ST7789](solinnovay/Python_ST7789) and adapted to work with a 170x320 display, adding offset and rotation as setup parameters.

Changed from using RPi.GPIO to lgpio to work better with gpiozero.

## Wiring
|LCD Pin|Pin     |Pin name|Labelled |
|-------|--------|--------|------|
|GND    |    9   |Ground  |Ground|
|VCC    |    1   |5V Power|Vin   |
|SCL    |   23   |GPIO 11 |Clock |
|SDA    |   19   |GPIO 10 |Data In|
|RES    |   22   |GPIO 25 | |
|DC     |   18   |GPIO 24 |Data/Command |
|CS     |   29   |GPIO  8 |Chip select|
|BLK    |   38   |GPIO 20 |Backlight|

## Code setup example

Complete example in the examples folder: `hello-pi.py`

```python
# Configuration for GPIO pins using BCM numbering
dc_pin = 24
reset_pin = 25
backlight_pin = 20

# Initialize the display
disp = ST7789.ST7789(
    dc=dc_pin,
    led=backlight_pin,
    rst=reset_pin,
    width=170,
    height=320,
    rotation=90,
    offset_left=0,
    offset_top=35
)
```
To run the example code from within this folder:

```bash
# Create virtual environment and activate it
python -m venv .venv
source .venv/bin/activate

# Install this library and the dependencies (lgpio, Pillow, numpy and spidev)
pip install . 

# Run the example
python examples/hello-pi.py
```

If everything works out, it should display two colored rectangles and the text "Hello, pi!" for five seconds, then turn off the display.

## References
- [xartle/Python_ST7789](https://github.com/xartle/Python_ST7789) xartle's fork of Solinnovay's lib
- [pkkirilov/ST7789](https://github.com/pkkirilov/ST7789)
- [st7789-python](https://github.com/pimoroni/st7789-python) Pimoroni's lib
- [Technoblogy.com](http://www.technoblogy.com/show?3WAI) Tiny TFT Graphics Library 2