"""What every block shares."""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class FrameContext:
    """Everything the blocks share for one frame. Never sent anywhere as a whole:
    only the fixed labels in contracts/events.md leave this computer."""
    image: np.ndarray                             # BGR; already masked, then blurred by face_blur
    results: dict = field(default_factory=dict)   # block type -> that block's local result


class Block:
    """One OpenCV 5 step. process() reads ctx.image and stores its result in ctx.results."""
    type = ""

    def process(self, ctx):
        raise NotImplementedError
