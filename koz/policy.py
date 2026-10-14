"""Fixed safety rules in code (CLAUDE.md rule 1).

Recipes, imports and the planner cannot change anything here. The setting ranges live
in contracts/recipe.schema.json; this file holds what the schema can't say.
Numbers marked "proposed" are not measurements yet (contracts/events.md, OPEN-1)."""

# Every block a recipe may contain, in the only order allowed.
BLOCK_ORDER = ("privacy_guard", "face_blur", "color_finder", "motion_zone",
               "person_detector", "line_counter", "looming")
# Always the first two blocks, with nothing to tune.
LOCKED_BLOCKS = ("privacy_guard", "face_blur")

# What is built so far. Anything else is refused with UNSUPPORTED_CAPABILITY
# instead of being silently skipped.
BUILT_BLOCKS = frozenset({"privacy_guard", "face_blur", "color_finder", "person_detector", "line_counter"})
BUILT_BRAINS = frozenset({"none"})
BUILT_ACTIONS = frozenset({"dashboard"})

# Strict parsing of recipe text.
MAX_RECIPE_BYTES = 16 * 1024
MAX_RECIPE_DEPTH = 12

# Runtime limits (proposed).
MAX_FRAME_AGE_S = 0.5          # older than this when used -> outputs "unknown"
PRIVACY_RECHECK_S = 120.0      # scene check at start, then at least this often
PRIVACY_TIMEOUT_S = 5.0        # a slower scene check counts as failed
OBSERVATION_INTERVAL_S = 1.0   # at most one observation event per second
STATUS_INTERVAL_S = 1.0        # a status heartbeat at least this often while running

# color_finder: "center" means within this distance of the middle (0..1 across the frame).
TARGET_CENTER_HALF_WIDTH = 0.1

# Privacy guard: Places365 scene classes that stop the job (index in categories_places365.txt, name).
PRIVATE_SCENES = {
    "PRIVATE_BATHROOM": ((45, "bathroom"), (195, "jacuzzi/indoor"), (295, "sauna"), (303, "shower")),
    "PRIVATE_BEDROOM": ((51, "bedchamber"), (52, "bedroom"), (55, "berth"), (89, "childs_room"),
                        (124, "dorm_room"), (179, "hospital_room"), (182, "hotel_room"),
                        (196, "jail_cell"), (240, "nursery"), (363, "youth_hostel")),
    "PRIVATE_CHANGING_ROOM": ((126, "dressing_room"), (219, "locker_room")),
}
# Places365 has no toilet class; a toilet stall is a trial case (docs/TRIALS.md).
SCENE_PRIVATE_SUM_BLOCKS = 0.15   # proposed: private classes together this likely -> blocked
SCENE_MIN_TOP_PROB = 0.20         # proposed: below this, the scene is "uncertain" -> not approved

# line_counter (proposed). A followed person's number is forgotten this long after they
# were last seen (the contract allows at most 5 s), and a box must overlap its previous
# position at least this much (IoU) to count as the same person.
TRACK_FORGET_S = 2.0
TRACK_MIN_IOU = 0.2

# face_blur (proposed). A low score threshold blurs more: a false blur is safe, a missed face is not.
FACE_SCORE_THRESHOLD = 0.5
FACE_MARGIN = 0.25             # grow each face box by this share on every side
FACE_PIXEL_CELLS = 6           # each face becomes at most 6 x 6 flat squares...
FACE_MIN_CELL_PX = 4           # ...each at least 4 px wide, so a tiny face becomes one flat square
