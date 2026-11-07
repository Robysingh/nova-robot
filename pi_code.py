"""
Interactive Robotics for Aging and Cognitive Impairments: A Customisable Approach
 MSc Computer Science project, Swansea University (2025)

 Raspberry Pi 4 Code - has to be run from terminal within the virtual environment:
 source combined_env/bin/activate

 - Captures frames from the Pi camera
 - Runs DeepFace to detect the dominant facial emotion
 - Maps emotion -> single-character mood code ('1'..'7')
 - Sends corresponding mapperd code over serial to the Pico
 - Draws a box/label for visual feedback;
 - Captures audio using microphone for wake-word detection
 - Sends single-character command to Pico corresponding to the word
   detected (W="Nova", T= "Hey Nova")
 - Press 'q' or ctrl+C to exit

 Mood detected using DeepFace: angry, disgust, fear,
 happy, sad, surprise, neutral.
 
""" 
# Import necessary libraries
import cv2
import os
import time
import threading
import subprocess
from deepface import DeepFace
import serial
import pyaudio
import numpy as np
from openwakeword.model import Model


# --- Setup the Serial Connection with the Pico ---
# Opens /dev/ttyACM0 at 9600 baud - If unavailable, continues without serial
# Check in Thonny if it is actually "/dev/ttyACM0" - could be " /dev/ttyACM1"
try:
    pico_serial = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    print("Pico connected successfully")
except serial.SerialException as e:
    print(f"Error connecting to Pico: {e}")
    pico_serial = None
    
    
# --- CAMERA SETUP ---
# Captures frames to a temporary JPEG path that will be read by OpenCV
frame_path = "/tmp/frame.jpg"


# --- FUNCTIONS ---
# Send exactly one ASCII character ('1'..'7') to the Pico if the port is open
def send_mood_command(mood_char):
    if pico_serial and pico_serial.is_open:
        print(f"Pi 4 sending mood command: '{mood_char}'")
        pico_serial.write(mood_char.encode('utf-8'))

# Generic sender for other single-char commands (for wake-word detection)
def send_command(char):
    if pico_serial and pico_serial.is_open and isinstance(char, str) and len(char) == 1:
        print(f"Pi 4 sending command: '{char}'")
        pico_serial.write(char.encode('utf-8'))

        
# Continuously capture frames using rpicam-still
# Resolution can be adjusted
def capture_frames():
    while True:
        subprocess.run(["/usr/bin/rpicam-still", "-t", "1",
            "--width", "480", "--height", "360",
            "--nopreview", "-o", frame_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.1)


# wake-word thread
# Define .onnx wake word modelspath here
CUSTOM_MODEL_PATHS = [
    # "Hello_Friend.onnx",
    # "Hey_Cat.onnx",
    # "hay_kat.onnx",
    # "luhk__at__mee.onnx",
    "/home/robyksingh/combined_env/nao_va.onnx",
    "/home/robyksingh/combined_env/hay_nau_va.onnx"
]
WAKE_THRESHOLD = 0.5

# Map wake-word model (name - pico command) (single char)
WAKEWORD_TO_CMD = {
    "nao_va": "W",
    "hay_nau_va": "T",
}

# Wake-word function
def wakeword_listener():
    # Load the wake word detection models from the provided ONNX files
    print("Initializing openWakeWord with custom models")
    owwModel = Model(wakeword_models=CUSTOM_MODEL_PATHS, inference_framework="onnx")

    # Audio setup - configure PyAudio input streams
    pa = pyaudio.PyAudio()
    CHUNK = 1280
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    print("Opening default audio stream")
    stream = pa.open(format=FORMAT,
                     channels=CHANNELS,
                     rate=RATE,
                     input=True,
                     frames_per_buffer=CHUNK)

    print("\nListening for multiple wake words")
    
    # Main loop
    try:
        while True:
            # Read microphone audio chunk
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            # Convert raw audio bytes to NumPy array for the model
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            # Run prediction on the audio chunk
            prediction = owwModel.predict(audio_np)

            # Check prediction scores for each loaded model
            for model_name, score in prediction.items():
                if score > WAKE_THRESHOLD:
                    print(f"Wake word '{model_name}' detected! (Confidence: {score:.2f})")
                    
                    # Check for corresponding Pico command ("W" or "T")
                    cmd = WAKEWORD_TO_CMD.get(model_name)
                    if cmd:
                        send_command(cmd) #Send single-character command to Pico
                    #Reset model state after detection
                    owwModel.reset()
                    break
                
    except KeyboardInterrupt:
        print("\nStopping wake word listener")
    finally:
        # Cleanup
        print("Wake listener cleanup complete.")
        stream.stop_stream()
        stream.close()
        pa.terminate()


# Start the mood capture thread (daemon - so it exits when the main program is terminated)
threading.Thread(target=capture_frames, daemon=True).start()
print("Real-Time Emotion Detection Started")

# start the wake-word listener thread (daemon - so it exits when the main program is terminated)
threading.Thread(target=wakeword_listener, daemon=True).start()
print("Wake-word Detection Started")

# Last sent mood (for edge detection)
previous_mood = None

# FPS calculation to display on screen
frame_count = 0
start_time = time.time()

# Track last modification time
last_mod_time = 0

# Analyse only 1 frame every FRAME_SKIP for optimisation
FRAME_SKIP = 5 # Analyse 1 frame for every 5 captured
frame_counter = 0

# --- MAIN LOOP ---
# Reads the latest frame, runs emotion analysis, maps to code, sends to Pico, and overlays UI
while True:
    # Ensure the frame file exists before attempting to read
    if not os.path.exists(frame_path):
        time.sleep(0.1)
        continue

    # For optimisation - prevents reading a partially written image file
    mod_time = os.path.getmtime(frame_path)
    if mod_time == last_mod_time:
        time.sleep(0.05)
        continue
    last_mod_time = mod_time 

    # Load the most recent frame
    frame = cv2.imread(frame_path)
    if frame is None:
        continue

    # Count frames for FPS calculation and skip-interval logic.
    frame_count += 1
    frame_counter += 1

    # Optimisation - if the frame counter is at the skip interval
    if frame_counter >= FRAME_SKIP:
        frame_counter = 0 # Reset the counter
        try:
            # Optimisation - use faster 'ssd' backend
            results = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='ssd' # Use lightweight SSD backend
            )
                       
            if not isinstance(results, list):
                results = [results] if results is not None else []
            if not results:
                raise ValueError("No faces detected")
            
            for face in results:
                emotion = face['dominant_emotion']
                region = face['region']

            # Only send when the emotion changes (rising-edge)
            if emotion != previous_mood:
                # single character mood code mapping
                if emotion == "happy":
                    send_mood_command('1')
                elif emotion == "sad":
                    send_mood_command('2')
                elif emotion == "angry":
                    send_mood_command('3')
                elif emotion == "fear":
                    send_mood_command('4')
                elif emotion == "surprise":
                    send_mood_command('5')
                elif emotion == "disgust":
                    send_mood_command('6')
                elif emotion == "neutral":
                    send_mood_command('7')
                
                previous_mood = emotion  # Update previous_mood

                # Draw bounding box + label for visual feedback
                region = face['region']
                cv2.rectangle(frame, (region['x'], region['y']), (region['x'] + region['w'], region['y'] + region['h']), (0, 255, 0), 2)
                cv2.putText(frame, emotion, (region['x'], region['y'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                
        except Exception as e:
        # If no face is detected or analysis fails set the default mood to neutral
            if previous_mood != "neutral":
                 send_mood_command('7')  # Neutral
                 previous_mood = "neutral"

    # Display the FPS and the frame
    elapsed_time = time.time() - start_time
    fps = frame_count / elapsed_time if elapsed_time > 0 else 0
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # Display emotion on screen 
    if previous_mood:
        cv2.putText(frame, f"Emotion: {previous_mood}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)


    cv2.imshow("Emotion Detection", frame)

    # Press 'q' to quit.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup when code execution is stopped
cv2.destroyAllWindows()
