# Nova: a customisable robot companion for dementia care

**MSc Computer Science dissertation, Swansea University (2025) · Mark: 87%**

Supervisor: Dr Deepak Sahoo

<p align="center">
  <img src="https://robysingh.github.io/nova-front.jpg" alt="Nova, a plush robot dog" width="320">
  <img src="https://robysingh.github.io/nova-sensors.png" alt="Nova's touch sensors and moving parts" width="420">
</p>

Nova is a low-cost socially assistive robot dog for older adults and people living with dementia. Commercial robot pets such as PARO and Joy for All are expensive and repeat the same fixed behaviour, so users lose interest over time. Nova lets the user choose how it sounds when it is stroked, and it changes those sounds to suit the user's mood.

I built it from scratch inside a £10 dog puppet, for about **£135** in total.

**Demo videos:** [Video 1](https://www.youtube.com/shorts/z6o6pgn4Ftw) · [Video 2](https://www.youtube.com/shorts/ZIG6oqubzOs) · [Video 3](https://www.youtube.com/shorts/6OWX88xoWI4)

**Portfolio:** https://robysingh.github.io

---

## What it does

| Input | Nova's response |
|-------|-----------------|
| Stroke its **body** | Moves its head and plays the sound chosen for the current mood |
| Stroke its **head** | Moves its tail and plays the sound chosen for the current mood |
| Touch its **cheek** | Plays a fixed sound |
| Say **"Nova"** | Shakes its head and plays a sound |
| Say **"Hey Nova"** | Plays a sound |
| Your **facial expression** | Sets the mood (7 emotions) that decides which sounds play |

Before using Nova, the user listens to 13 sound clips and picks which one plays for each touch and mood. That customisation is the core idea: the robot behaves the way its owner wants instead of repeating one fixed routine.

## How it works

```
                 Raspberry Pi 4                           Raspberry Pi Pico (MicroPython)
 Camera ──►  ┌───────────────────────────┐  USB serial  ┌────────────────────────────────┐
             │ DeepFace emotion, SSD     │  one char    │ 3 capacitive touch sensors     │
 INMP441 ──► │   backend, every 5th frame│ ───────────► │ 2 servos: head, tail (50 Hz)   │
 mic         │ openWakeWord, 2 custom    │  per event   │ MAX98357A I2S amp → speaker    │
             │   models, threshold 0.5   │              │   16 kHz, 16-bit mono          │
             └───────────────────────────┘              └────────────────────────────────┘
```

The two boards split the work. The Pi 4 runs the perception models in two threads (camera and microphone), and the Pico handles the real-time I/O so touch responses stay quick.

The Pi 4 sends one character over USB serial for each event, and only when something changes:

| Code | Meaning | Code | Meaning |
|------|---------|------|---------|
| `1` | happy | `5` | surprise |
| `2` | sad | `6` | disgust |
| `3` | angry | `7` | neutral (also sent when no face is found) |
| `4` | fear | `W` | wake word "Nova" |
| | | `T` | wake word "Hey Nova" |

### Touch sensing without a touch chip

Each touch sensor is a do-it-yourself capacitive sensor: a charge pin drives the pad through a large resistor (4.2 to 7 MΩ), and the Pico counts how long the sense pin takes to go high. A finger adds capacitance, so the count rises. The code averages five readings per sensor and compares them with a calibrated threshold, and it only reacts on a new touch (edge detection), not while a hand rests on the dog.

## Hardware

| Component | Approx. cost (GBP) |
|-----------|-------------------:|
| Raspberry Pi 4 | 50 |
| Raspberry Pi Pico | 6 |
| Camera module | 15 |
| INMP441 microphone | 3 |
| Servo motors (head, tail) | 20 |
| MAX98357A I2S amplifier | 6 |
| Speaker, 3 W 8 Ω | 5 |
| Dog puppet | 10 |
| Other (wires, resistors, fixings) | 20 |
| **Total** | **135** |

### Wiring

<p align="center">
  <img src="https://robysingh.github.io/nova-schematic.png" alt="Wiring schematic: Pico, servos, MAX98357A amplifier and touch sensors" width="560">
</p>

| Function | Pico GPIO |
|----------|-----------|
| Body touch (charge, sense) | 14, 15 |
| Head touch (charge, sense) | 16, 17 |
| Cheek touch (charge, sense) | 18, 19 |
| Tail servo | 10 |
| Head servo | 11 |
| I2S BCLK, LRC, DIN | 7, 8, 6 |

<p align="center">
  <img src="https://robysingh.github.io/nova-electronics.jpg" alt="Prototype electronics on a breadboard inside the dog" width="320">
</p>

## Code

| File | Runs on | What it does |
|------|---------|--------------|
| `pi_code.py` | Raspberry Pi 4 | Captures camera frames, detects the dominant emotion with DeepFace, listens for the wake words with openWakeWord, and sends event codes to the Pico |
| `pico_code.py` | Raspberry Pi Pico | Reads the three touch sensors, drives the servos, and plays mood-dependent sounds over I2S |
| `DigitalAudioLoop.py` | Raspberry Pi Pico | Plays all 13 sounds in turn so the user can choose their favourites |
| `requirements.txt` | Raspberry Pi 4 | Python packages for `pi_code.py` |

Not included: the 13 `.raw` sound clips (16 kHz, 16-bit mono, stored on the Pico) and the two custom wake-word models (`nao_va.onnx`, `hay_nau_va.onnx`). You can train your own wake words with [openWakeWord](https://github.com/dscripka/openWakeWord).

### Running it

1. Copy `pico_code.py` and the sound clips to the Pico and run it with MicroPython (for example from Thonny).
2. On the Pi 4, install the packages in a virtual environment: `pip install -r requirements.txt`
3. Set the wake-word model paths in `pi_code.py`, check the Pico's serial port (usually `/dev/ttyACM0`), and run `python3 pi_code.py`. Press `q` to quit.

## Evaluation

Ten participants took the Negative Attitudes Toward Robots Scale (NARS) before and after customising and interacting with Nova, followed by a semi-structured interview.

- Negative attitudes fell on all three NARS subscales after the interaction.
- The drop on the **emotions** subscale was statistically significant (Wilcoxon signed-rank, p = .007, large effect r = .85). The other two subscales fell but not significantly.
- In interviews, participants valued the customisation most and saw clear potential for older adults, while pointing out technical flaws to fix.

**Limitations:** most participants were young adults rather than the target users, the sample was small, and the prototype still has visible hardware and touch calibration issues.

## Future work

Smaller and more varied designs (for example a cat or seal), fully hidden electronics, extra movements, richer customisation, and a study with older adults and people living with dementia.

## Author

**Roby Karan Singh**: BEng Electronic & Electrical Engineering (First Class), MSc Computer Science (Distinction), Swansea University.
[Portfolio](https://robysingh.github.io) · [LinkedIn](https://www.linkedin.com/in/roby-ksingh/)
