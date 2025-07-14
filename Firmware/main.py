"""ILI9341 demo (clear)."""
from time import sleep, ticks_ms

import machine

from ili9341 import Display, color565
from machine import Pin, SPI, Timer # type: ignore
import gc
import time
import utime
import framebuf

from xglcd_font import XglcdFont

current_seconds = utime.time()

spi = SPI(0,
              baudrate=10000000,
              polarity=1,
              phase=1,
              bits=8,
              firstbit=SPI.MSB,
              sck=Pin(18),
              mosi=Pin(19),
              miso=Pin(16))
display = Display(spi, dc=Pin(15), cs=Pin(17), rst=Pin(14))

adcpin = 4
sensor = machine.ADC(adcpin)

def ReadTemp():
    adc_value = sensor.read_u16()
    volt = (3.3/65535)*adc_value
    temperature = 27 - (volt-0.706)/0.001721
    return round(temperature, 1)

# background_colors = [color565(0,0,0), color565(167, 80,120),color565(68,187,120),color565(200,180,130) color565(135,130,200)]


colors = {
    "GRAY": (189, 188, 193),
    "DARK GRAY": (132, 132, 135),
    "DARKER GRAY": (76, 75, 77),
    "LIGHT GRAY": (209, 208, 212),
    "LIGHTER GRAY": (235, 235, 236),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW": (255, 255, 0),
    "AQUA": (0, 255, 255),
    "MAROON": (128, 0, 0),
    "DARK_GREEN": (0, 128, 0),
    "NAVY": (0, 0, 128),
    "TEAL": (0, 128, 128),
    "PURPLE": (128, 0, 128),
    "ORANGE": (255, 128, 0),
    "DEEP_PINK": (255, 0, 128),
    "CYAN": (128, 255, 255),
}

button0 = Pin(0, Pin.IN, Pin.PULL_UP) # clock up
button1 = Pin(1, Pin.IN, Pin.PULL_UP) # clock swap
button2 = Pin(2, Pin.IN, Pin.PULL_UP)
button3 = Pin(3, Pin.IN, Pin.PULL_UP)
button4 = Pin(4, Pin.IN, Pin.PULL_UP) # clock down
button5 = Pin(5, Pin.IN, Pin.PULL_UP)
button6 = Pin(6, Pin.IN, Pin.PULL_UP)
button7 = Pin(7, Pin.IN, Pin.PULL_UP)

prev_button_1 = False

clock_shift = 0
clock_state = 0 # 0: not editing - 1: editing hours - 2: editing minutes


button0_hold_start = 0
button4_hold_start = 0
hold_delay_clock = 500  # delay before rapid-fire starts
rapid_fire_interval_clock = 50  # between rapid-fire adjustments

button3_hold_start = 0
button7_hold_start = 0
hold_delay_timer = 500  # delay before rapid-fire starts
rapid_fire_interval_timer = 50

time_alter = 0


prev_button_2 = False

start_time = 0
timer_time = 300
timer_running = False

display.clear(color565(0,0,0))

while True:

    temperature = str(ReadTemp())

    display.draw_text8x8(230, 285, temperature, color565(223,223,123), color565(0,0,0),90)



    current_seconds = utime.time()

    current_time_ms = utime.ticks_ms()  # Get current time in ms

    # CLOCK --------------------

    button1_current = not button1.value()

    if clock_state == 0:
        time_alter = 0
        display.draw_rectangle(135, 64, 1, 16, color565(0, 0, 0))
        if button1_current and not prev_button_1:  # Button just pressed
            clock_state = 1

    elif clock_state == 1:
        time_alter = 3600
        display.draw_rectangle(135, 40, 1, 16, color565(255, 255, 255))
        if button1_current and not prev_button_1:  # Button just pressed
            clock_state = 2

    elif clock_state == 2:
        time_alter = 60
        display.draw_rectangle(135, 40, 1, 16, color565(0, 0, 0))
        display.draw_rectangle(135, 64, 1, 16, color565(255, 255, 255))
        if button1_current and not prev_button_1:  # Button just pressed
            clock_state = 0

    prev_button_1 = False



    # Button 2 (Increase time)
    if not button0.value():
        if button0_hold_start == 0:
            clock_shift += time_alter
            button0_hold_start = current_time_ms
            last_rapid_fire_time = current_time_ms
        else:
            if utime.ticks_diff(current_time_ms, button0_hold_start) > hold_delay_clock:
                if utime.ticks_diff(current_time_ms, last_rapid_fire_time) >= rapid_fire_interval_clock:
                    clock_shift += time_alter
                    last_rapid_fire_time = current_time_ms
    else:
        button0_hold_start = 0


    if not button4.value():
        if button4_hold_start == 0:
            clock_shift -= time_alter
            button4_hold_start = current_time_ms
            last_rapid_fire_time = current_time_ms
        else:

            if utime.ticks_diff(current_time_ms, button4_hold_start) > hold_delay_clock:

                if utime.ticks_diff(current_time_ms, last_rapid_fire_time) >= rapid_fire_interval_clock:
                    clock_shift -= time_alter
                    last_rapid_fire_time = current_time_ms
    else:
        button4_hold_start = 0

    # Update time
    adjusted_seconds = utime.time() + clock_shift

    time_tuple = utime.localtime(adjusted_seconds)
    hours_minutes = "{:02d}:{:02d}".format(time_tuple[3], time_tuple[4])
    display.draw_text8x8(140, 40, hours_minutes, color565(223,223,123), color565(0,0,0), 90)
    #display.draw_text8x8(140, 40, str(adjusted_seconds), color565(223,223,123), color565(0,0,0), 90)
    # display.draw_text8x8(140, 180, str(clock_state) + "   +   " + str(time_alter), 50000, 0, 90)

    # TIMER ------------------

    button2_current = not button2.value()

    # Start timer when button is pressed and timer is not running
    if not timer_running and button2_current and not prev_button_2:
        start_time = current_seconds
        timer_running = True

    # Stop timer when button is pressed and timer is running
    elif timer_running and button2_current and not prev_button_2:
        timer_time = display_time
        timer_running = False

    # Button 3 (Increase time)
    if not button3.value():
        timer_running = False
        timer_time -= timer_time % 60
        if button3_hold_start == 0:
            timer_time += 60
            button3_hold_start = current_time_ms
            last_rapid_fire_time = current_time_ms
        else:
            if utime.ticks_diff(current_time_ms, button3_hold_start) > hold_delay_timer:
                if utime.ticks_diff(current_time_ms, last_rapid_fire_time) >= rapid_fire_interval_timer:
                    timer_time += 60
                    last_rapid_fire_time = current_time_ms
    else:
        button3_hold_start = 0


    if not button7.value():
        timer_running = False
        timer_time -= timer_time % 60
        if button7_hold_start == 0:
            timer_time -= 60
            button7_hold_start = current_time_ms
            last_rapid_fire_time = current_time_ms
        else:
            if utime.ticks_diff(current_time_ms, button7_hold_start) > hold_delay_timer:
                if utime.ticks_diff(current_time_ms, last_rapid_fire_time) >= rapid_fire_interval_timer:
                    timer_time -= 60
                    last_rapid_fire_time = current_time_ms
    else:
        button7_hold_start = 0


    # Display logic
    if not timer_running:
        display_time = timer_time


    else:
        delta_time = current_seconds - start_time
        display_time = timer_time - delta_time

    minutes = display_time // 60
    seconds = display_time % 60
    mm_ss = "{:02d}:{:02d}".format(minutes, seconds)

    display.draw_text8x8(140, 240, mm_ss + "  ", color565(223,223,123), color565(0,0,0), 90)


    prev_button_1 = button1_current
    prev_button_2 = button2_current
    utime.sleep_ms(10)  # Small delay to reduce CPU usage+