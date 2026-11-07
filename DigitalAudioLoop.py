"""
Interactive Robotics for Aging and Cognitive Impairments: A Customisable Approach
 MSc Computer Science project, Swansea University (2025)
 
 The code loops through 13 different sounds. The user can customise the robot by
 selecting which of these tracks they would like to hear during interaction.
 
"""
import machine

# List of audio files
AUDIO_FILES = [
    "01.raw",
    "02.raw",
    "03.raw",
    "04.raw",
    "05.raw",
    "06.raw",
    "07.raw",
    "08.raw",
    "09.raw",
    "10.raw",
    "11.raw",
    "12.raw",
    "13.raw"
]

#Sample rate of 16kHz
SAMPLE_RATE = 16000

# I2S pin configuration
I2S_BCLK_PIN = 7
I2S_LRC_PIN = 8
I2S_DIN_PIN = 6

# Configure the I2S output
audio_out = machine.I2S(
    0,
    sck=machine.Pin(I2S_BCLK_PIN),
    ws=machine.Pin(I2S_LRC_PIN),
    sd=machine.Pin(I2S_DIN_PIN),
    mode=machine.I2S.TX,
    bits=16,
    format=machine.I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=8192
)

read_buffer = bytearray(1024)

try:
    # Main loop
    while True:
        # Loop through each file
        for audio_file in AUDIO_FILES:
            print(f"Playing {audio_file}...")
            # Read file as binary
            with open(audio_file, "rb") as f:
                while True:
                    # Read a chunk of the file into the buffer
                    bytes_read = f.readinto(read_buffer)
                    # If no more bytes are read it means end of the file is reached
                    if bytes_read == 0:
                        break
                    # Write the audio data to the I2S peripheral
                    audio_out.write(read_buffer[:bytes_read])

finally:
    # Clean up I2S peripheral
    audio_out.deinit()
