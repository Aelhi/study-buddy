import board
from digitalio import DigitalInOut, Direction, Pull
import time
import pwmio


# Segment pins (A, B, C, D, E, F, G)
segment_pins = [board.D12, board.D8, board.D5, board.D3, board.D2, board.D11, board.D6]
segments = []

# Digit pins (D1 to D4)
digit_pins = [board.D13, board.D10, board.D9, board.D7]
digits = []

# Decimal Pin
decimal = DigitalInOut(board.D4)
decimal.direction = Direction.OUTPUT
decimal.value = True # Off for common anode display

# LEDs
red_led = DigitalInOut(board.A3)
red_led.direction = Direction.OUTPUT
red_led.value = False

blue_led = DigitalInOut(board.A2)
blue_led.direction = Direction.OUTPUT
blue_led.value = False

green_led = DigitalInOut(board.A1)
green_led.direction = Direction.OUTPUT
green_led.value = False

white_led = DigitalInOut(board.A0)
white_led.direction = Direction.OUTPUT
white_led.value = False

# Passive Buzzer
buzzer = pwmio.PWMOut(board.A4, duty_cycle=0, frequency=220, variable_frequency=True) # Uses PWM to control frequency/volume
buzzer_on = False
buzzer_end_time = 0

# Button
button = DigitalInOut(board.A5)
button.direction = Direction.INPUT
button.pull = Pull.UP
button_state = False

# Number segment pattern for common anode (0 = ON, 1 = OFF)
numbers = [
    [0,0,0,0,0,0,1],  # 0
    [1,0,0,1,1,1,1],  # 1
    [0,0,1,0,0,1,0],  # 2
    [0,0,0,0,1,1,0],  # 3
    [1,0,0,1,1,0,0],  # 4
    [0,1,0,0,1,0,0],  # 5
    [0,1,0,0,0,0,0],  # 6
    [0,0,0,1,1,1,1],  # 7
    [0,0,0,0,0,0,0],  # 8
    [0,0,0,0,1,0,0],  # 9
]

# Setup segments as outputs
for pin in segment_pins:
    seg = DigitalInOut(pin)
    seg.direction = Direction.OUTPUT
    seg.value = True  # Common Anode: OFF = True
    segments.append(seg)

# Setup digits as outputs
for pin in digit_pins:
    dig = DigitalInOut(pin)
    dig.direction = Direction.OUTPUT
    dig.value = False  # Common Anode: OFF = False
    digits.append(dig)


# Turns off all segments on display
def clear_segments():
    # """
    # Turns off all segments on display

    # :param None:

    # :return None
    # """
    for seg in segments:
        seg.value = True  # Common Anode: True = OFF


# Display specific number on a specific digit position
def display_digit(digit_index, number):
    # """
    # Displays a specific number on a specific digit position

    # :param int digit_index: the index of which digit on the display is being set
    # :param int number: the number to be set on the display segment

    # :return None
    # """
    for d in digits:
        d.value = False

    # Set segments for number
    for i, val in enumerate(numbers[number]):
        segments[i].value = val

    # Turn on decimal only for digit 1 (second digit from the left)
    if digit_index == 1:
        decimal.value = False  # ON (Common Anode)
    else:
        decimal.value = True   # OFF

    digits[digit_index].value = True
    time.sleep(0.003)
    digits[digit_index].value = False
    decimal.value = True  # turn off DP after digit refresh


# Displays 4 digit number through rapid cycling and multiplexing
def display_number(value_list):
    # """
    # Displays 4 digit number through rapid cycling and multiplexing

    # :param list value_list: the values to be displayed on the digit

    # :return None
    # """
    for i in range(4):
        display_digit(i, value_list[i])
    set_decimal(False)


# Controls decimal point
def set_decimal(on):
    # """
    # Displays 4 digit number through rapid cycling and multiplexing

    # :param boolean on: For common anode True=OFF, False=ON, so we invert the 'on' parameter

    # :return None
    # """
    decimal.value = not on


# Controls buzzer during last 3 seconds of each timer cycle
def handle_buzzer(current_time, timer_seconds):
    # """
    # Controls buzzer during last 3 seconds of each timer cycle

    # :param int current_time: Measures passed time on micro
    # :param int timer_seconds: Measures left on timer

    # :return None
    # """
    global buzzer_on, buzzer_end_time # Tracks buzzer state
    if 0 < timer_seconds <= 3 and not buzzer_on: # Turns on buzzer
        buzzer.frequency = 1200
        buzzer.duty_cycle = 32767
        buzzer_on = True
        buzzer_end_time = current_time + 0.2
    elif buzzer_on and current_time >= buzzer_end_time: # Turns off buzzer
        buzzer.duty_cycle = 0
        buzzer_on = False


# Turns off all outputs (LEDs, buzzer, dislpay)
def turn_everything_off():
    # """
    # Turns off all outputs (LEDs, buzzer, dislpay)

    # :param None

    # :return None
    # """
    white_led.value = False
    red_led.value = False
    blue_led.value = False
    green_led.value = False
    buzzer.duty_cycle = 0
    clear_segments()


# Runs study timer based of specified minutes
def study_timer(minutes = 25):
    # """
    # Runs study timer based of specified minutes

    # :param int minutes: The set amount time for the study timer

    # :return boolean: Indicates timer has finished successfully or was stopped
    # """
    global buzzer_on, buzzer_end_time
    flash_timer = 0
    flash_interval = 0.2
    white_led.value = True
    study_seconds = minutes * 60
    cancel_ready = False  # Prevent canceling until button released

    while study_seconds >= 0: 
        mins = study_seconds // 60
        secs = study_seconds % 60
        digits_to_show = [
            mins // 10,
            mins % 10,
            secs // 10,
            secs % 10
        ]
        start = time.monotonic() # Records run time to track for exactly 1 second

        while time.monotonic() - start < 1: # Continously displays digits and checks for button presses each second
            current_time = time.monotonic()
            display_number(digits_to_show)

            # Enable cancel after button was released
            if not button.value:
                cancel_ready = True

            # Cancel if button is pressed again after release
            if cancel_ready and button.value:
                turn_everything_off()
                white_led.value = False
                return False

            # Flashes red LED to indicate last 10 seconds
            if study_seconds <= 10:
                if current_time - flash_timer >= flash_interval:
                    red_led.value = not red_led.value
                    flash_timer = current_time
            else:
                red_led.value = False

            handle_buzzer(current_time, study_seconds) # Handles buzzer for last 3 seconds of timer

        study_seconds -= 1 # Decreases time by 1 second

    white_led.value = False
    return True


# Runs break timer based of specificed minutes
def break_timer(minutes = 5):
    # """
    # Runs break timer based of specified minutes

    # :param int minutes: The set amount time for the study timer

    # :return boolean: Indicates timer has finished successfully or was stopped
    # """
    global buzzer_on, buzzer_end_time
    flash_timer = 0
    flash_interval = 0.2
    white_led.value = True
    blue_led.value = True
    green_led.value = True
    break_seconds = minutes * 60
    cancel_ready = False  # Only allow cancel after button has been released once

    while break_seconds >= 0:
        minutes = break_seconds // 60
        seconds = break_seconds % 60
        digits_to_show = [
            minutes // 10,
            minutes % 10,
            seconds // 10,
            seconds % 10
        ]
        start = time.monotonic() # Records run time to track for exactly 1 second

        while time.monotonic() - start < 1: # Continously displays digits and checks for button presses each second
            current_time = time.monotonic()
            display_number(digits_to_show)

            # Only check for cancel if user has released the button first
            if not button.value:
                cancel_ready = True  # Now we are ready to detect a cancel press

            if cancel_ready and button.value:  # Now a second press
                turn_everything_off()
                white_led.value = False
                blue_led.value = False
                green_led.value = False
                return False  # Exit early

            # Flashes red LED to indicate last 10 seconds
            if break_seconds <= 10:
                if current_time - flash_timer >= flash_interval:
                    red_led.value = not red_led.value
                    flash_timer = current_time
            else:
                red_led.value = False

            handle_buzzer(current_time, break_seconds) # Handles buzzer for last 3 seconds of timer

        break_seconds -= 1 # Decreases time by 1 second

    # Time completed normally
    turn_everything_off()
    return True


last_button_state = False  # Tracks button's previous state for edge detection and debounce handling
system_state = False # Tracks if system is currently ON or OFF

while True: #Runs continuously as Adafruit METRO M0 Express is ON 
    button_state = button.value

    # Detect rising edge (button press)
    if button_state and not last_button_state:
        if system_state:
            # Turn everything off if already running
            turn_everything_off()
            system_state = False
        else:
            system_state = True

            # Run timers in a loop until cancelled
            while system_state:
                timer_completed = study_timer()

                if not timer_completed: # Turns off system if study timer cancelled
                    system_state = False
                    break

                timer_completed = break_timer()

                if not timer_completed: # Turns off system if break timer cancelled
                    system_state = False
                    break

            system_state = False #Ensures system is turned off

    last_button_state = button_state # Remembers button state for edge detection and debounce 
    time.sleep(0.05) # Delay for debounce and processing