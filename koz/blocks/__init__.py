"""OpenCV 5 blocks. Each block reads the frame and writes its local result."""
from .base import Block, FrameContext
from .color_finder import ColorFinder, Target
from .face_blur import FaceBlur, YuNetDetector
from .line_counter import Crossings, LineCounter
from .object_finder import ObjectFinder
from .person_detector import Detection, NanoDet, NanoDetPersons, Person, PersonDetector

# Blocks a recipe may add after the two locked ones (privacy_guard is the runner's gate).
TASK_BLOCKS = {ColorFinder.type: ColorFinder, ObjectFinder.type: ObjectFinder, PersonDetector.type: PersonDetector,
               LineCounter.type: LineCounter}

__all__ = ["Block", "FrameContext", "ColorFinder", "Target", "FaceBlur", "YuNetDetector",
           "Crossings", "Detection", "LineCounter", "NanoDet", "NanoDetPersons", "ObjectFinder", "Person", "PersonDetector",
           "TASK_BLOCKS"]
