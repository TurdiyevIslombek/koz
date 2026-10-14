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
BUILT_BLOCKS = frozenset({"privacy_guard", "face_blur", "color_finder"})
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

# face_blur (proposed). A low score threshold blurs more: a false blur is safe, a missed face is not.
FACE_SCORE_THRESHOLD = 0.5
FACE_MARGIN = 0.25             # grow each face box by this share on every side
FACE_PIXEL_CELLS = 6           # each face becomes at most 6 x 6 flat squares...
FACE_MIN_CELL_PX = 4           # ...each at least 4 px wide, so a tiny face becomes one flat square
