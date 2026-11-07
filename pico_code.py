"""
Interactive Robotics for Aging and Cognitive Impairments: A Customisable Approach
 MSc Computer Science project, Swansea University (2025)

 Raspberry Pi Pico Code
 The code can be run from Thonny

 The following code reads three capacitive touch sensors and:
 - Moves a head servo when the BODY sensor is touched and
   plays the corresponding sound based on the mood detected
 - Moves a tail servo when the HEAD sensor is touched and
   plays the corresponding sound based on the mood detected
 - Plays a predefined audio when the CHEEK sensor is touched
 - Waggles head if the word "Nova" is detected by the microphone
 - Plays a predefined sound if "Hey Nova" is detected by the microphone

 Mood is received over stdin (one char: '1'..'7')
 Wake word is received over stdin (W="Nova", T="Hey Nova")

"""

# Import necessary libraries
from machine import Pin, PWM, I2S
import utime
import sys
import select


# --- I/O PIN Setup ---
# BODY  (move head)
BODY_CHARGE_PIN = Pin(14, Pin.OUT)
BODY_SENSE_PIN  = Pin(15, Pin.IN)
# HEAD  (move tail)
HEAD_CHARGE_PIN = Pin(16, Pin.OUT)
HEAD_SENSE_PIN  = Pin(17, Pin.IN)
# CHEEK (play audio)
CHEEK_CHARGE_PIN = Pin(18, Pin.OUT)
CHEEK_SENSE_PIN  = Pin(19, Pin.IN)

# Servo outputs
TAIL_PIN = Pin(10)  # Controlled by HEAD sensor
HEAD_PIN = Pin(11)  # Controlled by BODY sensor

# I2S audio pins
I2S_BCLK_PIN = 7
I2S_LRC_PIN  = 8
I2S_DIN_PIN  = 6


# --- CONSTANTS ---
# Touch thresholds - to be calibrated
TOUCH_THRESHOLD_BODY  = 10
TOUCH_THRESHOLD_HEAD  = 30
TOUCH_THRESHOLD_CHEEK = 10

# Servo positions in nanoseconds - TAIL and HEAD
# Can be ajusted 
SERVO_REST_POS_TAIL   = 500000
SERVO_ACTIVE_POS_TAIL = 900000
SERVO_REST_POS_HEAD   = 50000
SERVO_ACTIVE_POS_HEAD = 1200000

# Audio
SAMPLE_RATE = 16000
AUDIO_IBUF  = 8192
AUDIO_CHUNK = 1024



# Mood audio file map/ dictionary
# Adjust based on user preference
MOOD_SOUNDS_BODY = {
    '1': "12.raw",  # Happy
    '2': "05.raw",  # Sad
    '3': "03.raw",  # Angry
    '4': "02.raw",  # Fear
    '5': "06.raw",  # Surprise
    '6': "07.raw",  # Disgust
    '7': "10.raw",  # Neutral
}

MOOD_SOUNDS_HEAD = {
    '1': "04.raw",  # Happy
    '2': "01.raw",  # Sad
    '3': "10.raw",  # Angry
    '4': "11.raw",  # Fear
    '5': "12.raw",  # Surprise
    '6': "06.raw",  # Disgust
    '7': "13.raw",  # Neutral
}

AUDIO_FILE_CHEEK = "11.raw"  # Fixed cheek sound

# Default mood
current_mood_mode = '7' # Neutral


# --- PWM SETUP ---
pwm_tail = PWM(TAIL_PIN)
pwm_head = PWM(HEAD_PIN)
pwm_tail.freq(50)
pwm_head.freq(50)


# --- FUNCTIONS ---
# Function to detect touch
def read_touch(charge_pin, sense_pin):
    """
    Reads the touch sensor/ capacitance
    Returns the time it takes for the sense pin to charge
    A high value indicates touch is detected
    """
    charge_pin.low()
    utime.sleep_ms(1)
    measurement = 0
    charge_pin.high()
    while sense_pin.value() == 0:
        measurement += 1
    return measurement

# Function to play audio
def play_audio(filename):
    """
    Plays a raw raw 16-bit mono audio via I2S
    """
    if not filename:
        print("Error: No audio file specified.")
        return
        
    print(f"Playing {filename}...")
    audio_out = I2S(
        0,
        sck=Pin(I2S_BCLK_PIN),
        ws=Pin(I2S_LRC_PIN),
        sd=Pin(I2S_DIN_PIN),
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=SAMPLE_RATE,
        ibuf=AUDIO_IBUF
    )
    read_buffer = bytearray(AUDIO_CHUNK)
    try:
        with open(filename, "rb") as f:
            while True:
                bytes_read = f.readinto(read_buffer)
                if bytes_read == 0:
                    break
                audio_out.write(read_buffer[:bytes_read])
    except OSError as e:
        print("Error playing file: {}. Ensure '{}' exists.".format(e, filename))
    finally:
        audio_out.deinit()
        print("Playback finished.")

# Shake Head function 
def shake_head(times=2, period_ms=350):
    for _ in range(times):
        pwm_head.duty_ns(SERVO_ACTIVE_POS_HEAD)
        utime.sleep_ms(period_ms // 2)
        pwm_head.duty_ns(SERVO_REST_POS_HEAD)
        utime.sleep_ms(period_ms // 2)


# --- INITIAL SETUP ---
# Move servos to resting positions
pwm_tail.duty_ns(SERVO_REST_POS_TAIL)
pwm_head.duty_ns(SERVO_REST_POS_HEAD)

# Track previous touch states - for edge detection
body_touched_previously = False
head_touched_previously = False
cheek_touched_previously = False


# --- MAIN LOOP ---
while True:
    # Mood/wake-word detection command check (sent from Pi 4)
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        command = sys.stdin.read(1) # Read single character
        if command in "1234567": 
            current_mood_mode = command
            print(f"Mood changed to: {current_mood_mode}")
        elif command == 'W': # wake-word: "Nova"
            print("Command: SHAKE HEAD")
            shake_head(times=3, period_ms=280)
            play_audio("02.raw")
        elif command == 'T': # wake-word: "Hey Nova"
            print("play sound 05.raw")
            play_audio("05.raw")

    # Read touch sensors using average - for better results
    NUM_READINGS = 5
    val1_sum, val2_sum, val3_sum = 0, 0, 0
    for _ in range(NUM_READINGS):
        val1_sum += read_touch(BODY_CHARGE_PIN, BODY_SENSE_PIN)
        val2_sum += read_touch(HEAD_CHARGE_PIN, HEAD_SENSE_PIN)
        val3_sum += read_touch(CHEEK_CHARGE_PIN, CHEEK_SENSE_PIN)
        utime.sleep_ms(5)
    touch1_value = val1_sum // NUM_READINGS
    touch2_value = val2_sum // NUM_READINGS
    touch3_value = val3_sum // NUM_READINGS

    print(f"BODY: {touch1_value}, HEAD: {touch2_value}, CHEEK: {touch3_value}")

    # BODY sensor logic - controls HEAD servo + sound
    is_body_touched_now = touch1_value > TOUCH_THRESHOLD_BODY
    if is_body_touched_now:
        pwm_head.duty_ns(SERVO_ACTIVE_POS_HEAD)
    else:
        pwm_head.duty_ns(SERVO_REST_POS_HEAD)
    
    if is_body_touched_now and not body_touched_previously:
        audio_file = MOOD_SOUNDS_BODY.get(current_mood_mode)
        play_audio(audio_file)
    body_touched_previously = is_body_touched_now

    # HEAD sensor logic - controls TAIL servo + sound
    is_head_touched_now = touch2_value > TOUCH_THRESHOLD_HEAD
    if is_head_touched_now:
        pwm_tail.duty_ns(SERVO_ACTIVE_POS_TAIL)
    else:
        pwm_tail.duty_ns(SERVO_REST_POS_TAIL)

    if is_head_touched_now and not head_touched_previously:
        audio_file = MOOD_SOUNDS_HEAD.get(current_mood_mode)
        play_audio(audio_file)
    head_touched_previously = is_head_touched_now

    # CHEEK sensor logic - plays fixed sound
    is_cheek_touched_now = touch3_value > TOUCH_THRESHOLD_CHEEK
    if is_cheek_touched_now and not cheek_touched_previously:
        play_audio(AUDIO_FILE_CHEEK)
    cheek_touched_previously = is_cheek_touched_now
    
    # Delay
    utime.sleep_ms(500)
