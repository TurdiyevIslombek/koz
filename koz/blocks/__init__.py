"""OpenCV 5 blocks. Each block reads the frame and writes its local result."""
from .base import Block, FrameContext
from .color_finder import ColorFinder, Target
from .face_blur import FaceBlur, YuNetDetector

# Blocks a recipe may add after the two locked ones (privacy_guard is the runner's gate).
TASK_BLOCKS = {ColorFinder.type: ColorFinder}

__all__ = ["Block", "FrameContext", "ColorFinder", "Target", "FaceBlur", "YuNetDetector", "TASK_BLOCKS"]
