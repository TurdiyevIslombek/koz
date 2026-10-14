"""The fixed error codes from contracts/events.md, section 11.

The code is what travels. The web app looks up the message by code and language,
so nothing here ever writes message text for the owner."""

CODES = frozenset({
    # rule 1: recipes and the agent loop
    "INVALID_RECIPE", "SAFETY_LOCKED", "ADJUSTMENT_LIMIT", "CHECK_FAILED", "PLANNER_UNAVAILABLE",
    # rules 2-3: privacy guard, face blur, scene-change tripwire (stretch)
    "PRIVATE_BATHROOM", "PRIVATE_TOILET", "PRIVATE_BEDROOM", "PRIVATE_CHANGING_ROOM",
    "PRIVACY_UNCERTAIN", "PRIVACY_UNAVAILABLE", "BLUR_UNAVAILABLE", "SCENE_CHANGED", "LENS_COVERED",
    # rules 4-12: requests Ko'z refuses, local setup, runtime safety
    "IDENTITY_FORBIDDEN", "PROFILING_FORBIDDEN", "SCHOOL_COUNTS_ONLY", "OWNERSHIP_REQUIRED",
    "ALLOWED_AREA_REQUIRED", "VIEW_FORBIDDEN", "AUDIO_FORBIDDEN", "FRAMES_FORBIDDEN", "INVALID_EVENT",
    "AUTH_REQUIRED", "FRAME_STALE", "OVERLOADED", "SOLE_PROTECTION_FORBIDDEN", "MOTOR_TARGET_FORBIDDEN",
    "ACTUATOR_FORBIDDEN", "MOTOR_NOT_ARMED", "MOTOR_SAFETY_STOP", "RETENTION_LOCKED",
    # protocol and general
    "UNSUPPORTED_CAPABILITY", "INVALID_COMMAND", "BUSY", "COMMAND_EXPIRED", "PROTOCOL_VERSION",
    "INTERNAL_ERROR",
})


class KozError(Exception):
    """A refusal or failure with a fixed code.

    `detail` is for the developer only and names a place or a reason we chose
    ("block order"), never values copied from the recipe or the camera."""

    def __init__(self, code, detail=""):
        if code not in CODES:
            raise ValueError(f"unknown error code {code!r}")
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
