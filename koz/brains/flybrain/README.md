# Fly brain (from Islombek's fly-brain car, stages 1–3)

`original/` holds unchanged copies of the files Ko'z needs from Islombek's own project
(`~/Downloads/flybrain_car`, the stage 1–3 car in his maker portfolio), copied on Oct 16, 2026.
Their SHA-256 checksums are in `original/ORIGINALS.sha256`, and `tests/test_flybrain_copy.py`
fails if any of them changes. **Never edit `original/`, and never write to the original folder.**
Ko'z's own fly-brain block is built next to it, from these copies: `brain.py` (the simulation, same spikes as
the original), `driver.py` (eyes → brain → wheels, same wheels as `brain_driver.py`) and `steering.py`
(option B: the ball's side becomes looming on the *other* eye, so the fly's own escape turn steers it
toward the ball).

A full backup of the original folder (without `.venv`) and the checksums of all 187 original files are in
`~/AI/competitions/_backups/flybrain_car_2026-10-16.zip` and `.sha256`.

| Copied file | What it is |
|---|---|
| `brain/flybrain.py` | Leaky integrate-and-fire simulation of fly neurons (constants from Shiu et al. 2024, *Nature*; wiring from the FlyWire connectome v783) |
| `brain/locomotion/` | The 2,282-neuron circuit the car uses: `neurons.json` (groups: looming eye neurons, DNa01/DNa02 steering, MDN backward, GF and DNp09), `weights.npz` (synapse counts), `positions.csv` (for drawing) |
| `common/brain_driver.py` | Sensor distances → eye firing rates → brain → wheel speeds (stages 2 and 3) |
| `common/reflex.py` | The hand-written stuck reflex on top of the brain |
| `stage2/stage2.py`, `stage3/stage3.py`, `stage3/vision.py` | Stage 2 (ultrasonic on a servo) and stage 3 (ESP32-CAM looming from optical flow) |
| `config.py` | All the tuned numbers |
| `arduino/car/car.ino`, `PINS.txt` | The car sketch (stage 1 rules, serial protocol, 300 ms watchdog) and the wiring |
| `requirements.txt` | What the original needs |

Licences (checked Oct 16): the Shiu et al. 2024 model code is MIT (Philip Shiu and Nico Spiller); the
FlyWire data the circuit comes from is CC BY-NC 4.0 (attribution, non-commercial). Credits: main README.
