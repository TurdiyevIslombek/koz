"""Settings for the fly-brain car. Change values here, not in the other files."""

# Arduino USB port. "auto" finds it. Or write it, e.g. "/dev/cu.usbmodem1101"
PORT = "wifi"

# Stage 3 camera.
#   "auto"    = the ESP32-CAM (http://flycar-cam.local:81/stream, then http://192.168.4.1:81/stream)
#   "webcam"  = the Mac's own camera (for testing)
#   or the full address, e.g. "http://192.168.1.50:81/stream"
CAMERA = "http://192.168.4.1:81/stream"
CAMERA_FLIP = True       # True if the camera is mounted upside down
CAMERA_MIRROR = False    # True if left and right are swapped in the picture

# Servo directions, degrees from straight ahead (+ = left). Must match LEFT_DEG / RIGHT_DEG in arduino/car/car.ino
SCAN_ANGLES = {"L": 60, "C": 0, "R": -60}

# Fly brain
TICK_MS = 50             # brain time per tick
SEED = 0

# Sensors -> eye neurons (LC4 + LPLC2)
MAX_HZ = 250.0           # strongest eye input
OBJ_CM = 20.0            # assumed obstacle width (turns distance into angular size)
LOOM_SAT = 2.0           # rad/s of growth that gives MAX_HZ
TOUCH_CM = 22.0          # closer than this always counts as maximum looming
STALE_S = 1.2            # a direction not measured for this long gives 0 looming

# Camera -> eye neurons
CAM_W, CAM_H = 160, 120  # small picture used for optical flow
EXP_SAT = 0.15           # expansion per frame that gives MAX_HZ

# Neurons -> wheels (DNa01 + DNa02 steering, MDN moonwalker)
BASE = 130               # forward drive when nothing is seen
K_TURN = 3.0             # wheel units per Hz of steering difference
K_BACK = 14.0            # wheel units per Hz of moonwalker firing
WINDOW_MS = 100          # how much recent spiking is read
