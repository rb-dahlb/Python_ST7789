# ST7789 IPS LCD (170x320) driver
import numbers
import time
import numpy as np

from PIL import Image
from PIL import ImageDraw

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

SPI_CLOCK_HZ = 40000000 # 40 MHz

# Constants for interacting with display registers.
ST7789_TFTWIDTH    = 170
ST7789_TFTHEIGHT   = 320

ST7789_NOP         = 0x00
ST7789_SWRESET     = 0x01
ST7789_RDDID       = 0x04
ST7789_RDDST       = 0x09
ST7789_RDDPM       = 0x0A
ST7789_RDDMADCTL   = 0x0B
ST7789_RDDCOLMOD   = 0x0C
ST7789_RDDIM       = 0x0D
ST7789_RDDSM       = 0x0E
ST7789_RDDSDR      = 0x0F

ST7789_SLPIN       = 0x10
ST7789_SLPOUT      = 0x11
ST7789_PTLON       = 0x12
ST7789_NORON       = 0x13

ST7789_INVOFF      = 0x20
ST7789_INVON       = 0x21
ST7789_GAMSET      = 0x26
ST7789_DISPOFF     = 0x28
ST7789_DISPON      = 0x29
ST7789_CASET       = 0x2A
ST7789_RASET       = 0x2B
ST7789_RAMWR       = 0x2C
ST7789_RAMRD       = 0x2E

ST7789_PTLAR       = 0x30
ST7789_VSCRDEF     = 0x33
ST7789_TEOFF       = 0x34
ST7789_TEON        = 0x35
ST7789_MADCTL      = 0x36
ST7789_VSCRSADD    = 0x37
ST7789_IDMOFF      = 0x38
ST7789_IDMON       = 0x39
ST7789_COLMOD      = 0x3A
ST7789_RAMWRC      = 0x3C
ST7789_RAMRDC      = 0x3E

ST7789_TESCAN      = 0x44
ST7789_RDTESCAN    = 0x45

ST7789_WRDISBV     = 0x51
ST7789_RDDISBV     = 0x52
ST7789_WRCTRLD     = 0x53
ST7789_RDCTRLD     = 0x54
ST7789_WRCACE      = 0x55
ST7789_RDCABC      = 0x56
ST7789_WRCABCMB    = 0x5E
ST7789_RDCABCMB    = 0x5F

ST7789_RDABCSDR    = 0x68

ST7789_RDID1       = 0xDA
ST7789_RDID2       = 0xDB
ST7789_RDID3       = 0xDC

ST7789_RAMCTRL     = 0xB0
ST7789_RGBCTRL     = 0xB1
ST7789_PORCTRL     = 0xB2
ST7789_FRCTRL1     = 0xB3

ST7789_GCTRL       = 0xB7
ST7789_DGMEN       = 0xBA
ST7789_VCOMS       = 0xBB

ST7789_LCMCTRL     = 0xC0
ST7789_IDSET       = 0xC1
ST7789_VDVVRHEN    = 0xC2

ST7789_VRHS        = 0xC3
ST7789_VDVSET      = 0xC4
ST7789_VCMOFSET    = 0xC5
ST7789_FRCTR2      = 0xC6
ST7789_CABCCTRL    = 0xC7
ST7789_REGSEL1     = 0xC8
ST7789_REGSEL2     = 0xCA
ST7789_PWMFRSEL    = 0xCC

ST7789_PWCTRL1     = 0xD0
ST7789_VAPVANEN    = 0xD2
ST7789_CMD2EN      = 0xDF5A6902
ST7789_PVGAMCTRL   = 0xE0
ST7789_NVGAMCTRL   = 0xE1
ST7789_DGMLUTR     = 0xE2
ST7789_DGMLUTB     = 0xE3
ST7789_GATECTRL    = 0xE4
ST7789_PWCTRL2     = 0xE8
ST7789_EQCTRL      = 0xE9
ST7789_PROMCTRL    = 0xEC
ST7789_PROMEN      = 0xFA
ST7789_NVMSET      = 0xFC
ST7789_PROMACT     = 0xFE

# Colours for convenience
ST7789_BLACK       = 0x0000 # 0b 00000 000000 00000
ST7789_BLUE        = 0x001F # 0b 00000 000000 11111
ST7789_GREEN       = 0x07E0 # 0b 00000 111111 00000
ST7789_RED         = 0xF800 # 0b 11111 000000 00000
ST7789_CYAN        = 0x07FF # 0b 00000 111111 11111
ST7789_MAGENTA     = 0xF81F # 0b 11111 000000 11111
ST7789_YELLOW      = 0xFFE0 # 0b 11111 111111 00000
ST7789_WHITE       = 0xFFFF # 0b 11111 111111 11111


def color565(r, g, b):
    """Convert red, green, blue components to a 16-bit 565 RGB value. Components
    should be values 0 to 255.
    """
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def image_to_data(image):
    """Generator function to convert a PIL image to 16-bit 565 RGB bytes."""
    # NumPy is much faster at doing this. NumPy code provided by:
    # Keith (https://www.blogger.com/profile/02555547344016007163)
    pb = np.array(image.convert('RGB')).astype('uint16')
    color = ((pb[:,:,0] & 0xF8) << 8) | ((pb[:,:,1] & 0xFC) << 3) | (pb[:,:,2] >> 3)
    return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()

class ST7789(object):
    """Representation of an ST7789 IPS LCD."""

    def __init__(self, spi, mode=3, rst=27, dc=25, led=24, gpio=None, width=ST7789_TFTWIDTH,
        height=ST7789_TFTHEIGHT, rotation=0, offset_left=0, offset_top=0):
        """Create an instance of the display using SPI communication.  Must
        provide the GPIO pin number for the D/C pin and the SPI driver.  Can
        optionally provide the GPIO pin number for the reset pin as the rst
        parameter.
        """
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._led = led
        self._gpio = gpio
        self.width = width
        self.height = height
        self.rotation = rotation

        self.offset_left = offset_left
        self.offset_top = offset_top

        if self._gpio is None:
            self._gpio = GPIO.get_platform_gpio()
        # Set DC as output.
        self._gpio.setup(dc, GPIO.OUT)
        # Setup reset as output (if provided).
        if rst is not None:
            self._gpio.setup(rst, GPIO.OUT)
        # Turn on the backlight LED
        self._gpio.setup(led, GPIO.OUT)
        self._gpio.setup(led, GPIO.HIGH)
        # Set SPI to mode 0, MSB first.
        spi.set_mode(mode)
        spi.set_bit_order(SPI.MSBFIRST)
        spi.set_clock_hz(SPI_CLOCK_HZ)
        # Create an image buffer.
        self.buffer = Image.new('RGB', (width, height))

    def send(self, data, is_data=True, chunk_size=4096):
        """Write a byte or array of bytes to the display. Is_data parameter
        controls if byte should be interpreted as display data (True) or command
        data (False).  Chunk_size is an optional size of bytes to write in a
        single SPI transaction, with a default of 4096.
        """
        # Set DC low for command, high for data.
        self._gpio.output(self._dc, is_data)
        # Convert scalar argument to list so either can be passed as parameter.
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]
        # Write data a chunk at a time.
        for start in range(0, len(data), chunk_size):
            end = min(start+chunk_size, len(data))
            self._spi.write(data[start:end])

    def command(self, data):
        """Write a byte or array of bytes to the display as command data."""
        self.send(data, False)

    def data(self, data):
        """Write a byte or array of bytes to the display as display data."""
        self.send(data, True)

    def reset(self):
        """Reset the display, if reset pin is connected."""
        if self._rst is not None:
            self._gpio.set_high(self._rst)
            time.sleep(0.100)
            self._gpio.set_low(self._rst)
            time.sleep(0.100)
            self._gpio.set_high(self._rst)
            time.sleep(0.100)

    def shutdown(self):
        """Send shutdown command to the display."""
        self.command(ST7789_DISPOFF)

    def _init(self):
        # Initialize the display.  Broken out as a separate function so it can
        # be overridden by other displays in the future.

        time.sleep(0.010)
        self.command(0x11)
        time.sleep(0.150)

        self.command(0x36)
        self.data(0x00)

        self.command(0x3A)
        self.data(0x05)

        self.command(0xB2)
        self.data(0x0C)
        self.data(0x0C)

        self.command(0xB7)
        self.data(0x35)

        self.command(0xBB)
        self.data(0x1A)

        self.command(0xC0)
        self.data(0x2C)

        self.command(0xC2)
        self.data(0x01)

        self.command(0xC3)
        self.data(0x0B)

        self.command(0xC4)
        self.data(0x20)

        self.command(0xC6)
        self.data(0x0F)

        self.command(0xD0)
        self.data(0xA4)
        self.data(0xA1)

        self.command(0x21)

        self.command(0xE0)
        self.data(0x00)
        self.data(0x19)
        self.data(0x1E)
        self.data(0x0A)
        self.data(0x09)
        self.data(0x15)
        self.data(0x3D)
        self.data(0x44)
        self.data(0x51)
        self.data(0x12)
        self.data(0x03)
        self.data(0x00)
        self.data(0x3F)
        self.data(0x3F)

        self.command(0xE1)
        self.data(0x00)
        self.data(0x18)
        self.data(0x1E)
        self.data(0x0A)
        self.data(0x09)
        self.data(0x25)
        self.data(0x3F)
        self.data(0x43)
        self.data(0x52)
        self.data(0x33)
        self.data(0x03)
        self.data(0x00)
        self.data(0x3F)
        self.data(0x3F)
        self.command(0x29)

        time.sleep(0.100) # 100 ms

    def begin(self):
        """Initialize the display.  Should be called once before other calls that
        interact with the display are called.
        """
        self.reset()
        self._init()
        
        # Add this to the begin() method after setting rotation
        if self.rotation == 90 or self.rotation == 270:
            # Swap width and height for window setting
            display_width = self.height
            display_height = self.width
        else:
            display_width = self.width
            display_height = self.height

        # Set rotation
        if self.rotation == 0:
            madctl = 0x00
        elif self.rotation == 90:
            madctl = 0x60
        elif self.rotation == 180:
            madctl = 0xC0
        elif self.rotation == 270:
            madctl = 0xA0
        else:
            madctl = 0x00
        
        self.command(0x36)  # MADCTL
        self.data(madctl)

        # Set window offset
        self.command(0x2A)  # Column address set
        self.data(0x00)
        self.data(self.offset_left)
        self.data(0x00)
        self.data(display_width + self.offset_left - 1)
        
        self.command(0x2B)  # Row address set
        self.data(0x00)
        self.data(self.offset_top)
        self.data(0x00)
        self.data(display_height + self.offset_top - 1)

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        """Set the pixel address window for proceeding drawing commands. x0 and
        x1 should define the minimum and maximum x pixel bounds.  y0 and y1
        should define the minimum and maximum y pixel bound.  If no parameters
        are specified the default will be to update the entire display from 0,0
        to width-1,height-1.
        """
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
            
        # Adjust for rotation
        if self.rotation == 90:
            x0, y0, x1, y1 = y0, self.width-1-x1, y1, self.width-1-x0
        elif self.rotation == 180:
            x0, y0, x1, y1 = self.width-1-x1, self.height-1-y1, self.width-1-x0, self.height-1-y0
        elif self.rotation == 270:
            x0, y0, x1, y1 = self.height-1-y1, x0, self.height-1-y0, x1
        
        # Add offsets
        x0 += self.offset_left
        x1 += self.offset_left
        y0 += self.offset_top
        y1 += self.offset_top
    
        self.command(ST7789_CASET)       # Column addr set
        self.data(x0 >> 8)
        self.data(x0)                    # XSTART
        self.data(x1 >> 8)
        self.data(x1)                    # XEND
        self.command(ST7789_RASET)       # Row addr set
        self.data(y0 >> 8)
        self.data(y0)                    # YSTART
        self.data(y1 >> 8)
        self.data(y1)                    # YEND
        self.command(ST7789_RAMWR)       # write to RAM

    #def display(self, image=None):
    def display(self, image=None, x0=0, y0=0, x1=None, y1=None):
        """Write the display buffer or provided image to the hardware.  If no
        image parameter is provided the display buffer will be written to the
        hardware.  If an image is provided, it should be RGB format and the
        same dimensions as the display hardware.
        """
        # By default write the internal buffer to the display.
        if image is None:
            image = self.buffer
        # Set address bounds to entire display.
        #self.set_window()
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.set_window(x0, y0, x1, y1)
        #image.thumbnail((x1-x0+1, y1-y0+1), Image.ANTIALIAS)
        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        pixelbytes = list(image_to_data(image))
        # Write data to hardware.
        self.data(pixelbytes)

    def clear(self, color=(0,0,0)):
        """Clear the image buffer to the specified RGB color (default black)."""
        width, height = self.buffer.size
        self.buffer.putdata([color]*(width*height))

    def draw(self):
        """Return a PIL ImageDraw instance for 2D drawing on the image buffer."""
        return ImageDraw.Draw(self.buffer)


