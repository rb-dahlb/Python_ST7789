import ST7789
import time
from PIL import Image, ImageDraw, ImageFont
import random

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

# Initialize display
disp.begin()

# After rotation, width and height are swapped for our image
if disp._rotation == 90 or disp._rotation == 270:
    img_width = 320
    img_height = 170
else:
    img_width = 170
    img_height = 320

# Create image with the appropriate dimensions
image = Image.new("RGB", (img_width, img_height), (random.randint(0,255), 100, 0))
draw = ImageDraw.Draw(image)

# Draw a rectangle
draw.rectangle((20, 20, img_width-20, img_height-20), outline=(255, 255, 255), fill=(0, 100, random.randint(0, 255)))

# Draw some text
text = "Hello, Pi!"
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
except IOError:
    font = ImageFont.load_default()

# Handle text rendering
try:
    bbox = font.getbbox(text)
    font_width = bbox[2] - bbox[0]
    font_height = bbox[3] - bbox[1]
except AttributeError:
    try:
        font_width, font_height = font.getsize(text)
    except:
        font_width, font_height = 100, 20

draw.text(
    (img_width // 2 - font_width // 2, img_height // 2 - font_height // 2),
    text,
    font=font,
    fill=(255, 255, 255)
)

# Display the image
disp.display(image)
print("Display test complete, turning off display in 5 seconds.")
time.sleep(5)
print("Display off.")
disp.shutdown()
disp.set_backlight(False)
disp.cleanup()
