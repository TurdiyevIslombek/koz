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
PRIVACY_RECHECK_S = 10.0       # scene check at start, then this often (one check takes ~10 ms)
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

# STRICT MODE ONLY (--strict, for schools and public cameras): the guard approves only these
# public and work places (Places365 names). Anything else, even something harmless like
# "catacomb", is "uncertain" and stops the job. The default mode (live test #3) runs anywhere
# and stops on what it sees; see DEFAULT_PRIVATE_* below and koz/privacy.py.
# Removed after the security review of Oct 14, because private rooms get mistaken for
# them (a dark bedroom came out as "staircase 0.36"): staircase, entrance_hall, home_office.
ALLOWED_SCENES = (
    # schools
    "classroom", "kindergarden_classroom", "lecture_room", "computer_room", "library/indoor",
    "art_school", "science_museum",
    # shops, markets, cafes
    "general_store/indoor", "general_store/outdoor", "supermarket", "market/indoor", "market/outdoor",
    "bazaar/indoor", "bazaar/outdoor", "department_store", "clothing_store", "shoe_shop", "bookstore",
    "candy_store", "drugstore", "fabric_store", "florist_shop/indoor", "gift_shop", "hardware_store",
    "jewelry_shop", "pet_shop", "toyshop", "bakery/shop", "butchers_shop", "shopfront",
    "shopping_mall/indoor", "flea_market/indoor", "delicatessen", "repair_shop", "coffee_shop",
    "fastfood_restaurant", "restaurant", "cafeteria", "food_court",
    # offices and work rooms
    "office", "office_cubicles", "conference_room", "reception", "waiting_room",
    # corridors and lobbies (only with SCENE_MIN_TOP_PROB_CAUTIOUS, see below)
    "corridor", "lobby", "elevator_lobby",
    # outside
    "street", "alley", "crosswalk", "parking_lot", "plaza", "courtyard", "yard", "driveway",
    "playground", "park",
    # farms
    "farm", "barn", "stable", "corral", "pasture", "field/cultivated", "orchard", "vegetable_garden",
)
# Measured on 46 Places365 validation photos plus darkened copies (docs/TRIALS.md, live test #1):
SCENE_PRIVATE_TOP5_BLOCKS = 0.10  # any private room in the top 5 above this -> blocked
SCENE_PRIVATE_SUM_BLOCKS = 0.15   # private rooms together this likely -> blocked
SCENE_MIN_TOP_PROB = 0.30         # the allowed top guess must be at least this sure
# Places that bathrooms and bedrooms are most often mistaken for (real bathroom: "corridor
# 0.11", "elevator_lobby 0.09"), so they must be much surer to be approved.
CAUTIOUS_SCENES = ("corridor", "lobby", "elevator_lobby")
SCENE_MIN_TOP_PROB_CAUTIOUS = 0.50
SCENE_MIN_BRIGHTNESS = 40         # 0..255 grey, over the allowed area: darker -> uncertain
SCENE_MIN_CONTRAST = 20           # standard deviation of that grey: flatter -> uncertain
CAMERA_WARMUP_S = 1.0             # a live camera's first frames are dark while exposure settles

# Object check (after live test #2: "a desk in a bedroom" is not "a bedroom"). The privacy
# guard also looks for things it can actually see, with NanoDet (COCO classes):
PRIVATE_OBJECTS = {"bed": (59, "PRIVATE_BEDROOM"), "toilet": (61, "PRIVATE_BATHROOM")}
SINK_CLASS = 71                       # COCO; a sink stops only together with SINK_ROOMS below
SINK_ROOMS = ("bathroom", "shower")   # ...in the room check's top 3
OBJECT_MIN_CONFIDENCE = 0.40
OBJECT_CHECKS_TO_STOP = 2             # seen in 2 of the last 3 checks -> stopped
OBJECT_CHECK_WINDOW = 3
# Default mode (no --strict): the room check stops only when it is confident; the object
# check and darkness do the rest. Measured on 71 real photos (docs/TRIALS.md, live test #3).
DEFAULT_PRIVATE_TOP_BLOCKS = 0.50   # a private room is the top guess at least this sure
DEFAULT_PRIVATE_SUM_BLOCKS = 0.40   # or private rooms together reach this

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
