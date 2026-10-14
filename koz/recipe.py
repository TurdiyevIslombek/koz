"""Load and check a recipe (CLAUDE.md rule 1; contracts/events.md section 3).

Every recipe goes through here: from the planner, from an adjustment and from an import.
The steps, in order:
  1. strict parsing (size, depth, duplicate keys, NaN/Infinity),
  2. the contract schema (contracts/recipe.schema.json),
  3. the checks the schema can't express (order, each block once, geometry),
  4. "is this built yet?".
Anything wrong raises KozError. Nothing is repaired or filled in. Error details name
only the place in the recipe, never the values inside it."""
import copy
import json
import math
from dataclasses import dataclass
from functools import lru_cache

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from . import CONTRACTS, policy
from .errors import KozError

# An alert template only makes sense with the block that produces it.
ALERT_NEEDS = {"motion_detected": "motion_zone", "count_changed": "person_detector"}


@dataclass(frozen=True)
class CheckedRecipe:
    """A recipe that passed every check. The runner accepts nothing else."""
    data: dict
    school: bool   # the school mode it was checked under (recipe flag OR local setup)


def load_recipe(raw, local_school=False):
    """Recipe text (str or bytes) -> CheckedRecipe, or KozError."""
    return check_recipe(parse_recipe_text(raw), local_school)


def parse_recipe_text(raw):
    """Turn recipe text into a dict, refusing anything unusual instead of guessing."""
    try:
        data = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
        if len(data) > policy.MAX_RECIPE_BYTES:
            raise KozError("INVALID_RECIPE", "too large")
        recipe = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
                            parse_constant=_no_constant, parse_float=_finite_float)
    except (UnicodeError, ValueError, RecursionError):   # JSON errors are ValueErrors
        raise KozError("INVALID_RECIPE", "not strict JSON") from None
    if _depth(recipe) > policy.MAX_RECIPE_DEPTH:
        raise KozError("INVALID_RECIPE", "nested too deep")
    return recipe


def check_recipe(recipe, local_school=False):
    """A parsed recipe -> CheckedRecipe, or KozError. Also used for every adjustment."""
    if not _all_finite(recipe):   # NaN slips through the schema's range checks
        raise KozError("INVALID_RECIPE", "a number is NaN or Infinity")
    _check_locked_blocks(recipe)
    validator = _validator()
    if not validator.is_valid(recipe):
        if _only_school_rules_broken(recipe):
            raise KozError("SCHOOL_COUNTS_ONLY")
        where = "/".join(str(p) for p in best_match(validator.iter_errors(recipe)).absolute_path)
        raise KozError("INVALID_RECIPE", f"schema, at /{where}")
    _check_order_and_geometry(recipe)
    school = recipe["privacy"]["school"] or local_school
    if school and not recipe["privacy"]["school"]:
        # A local school setting applies the school rules even if the recipe says otherwise.
        as_school = copy.deepcopy(recipe)
        as_school["privacy"]["school"] = True
        if not validator.is_valid(as_school):
            raise KozError("SCHOOL_COUNTS_ONLY")
    _check_built(recipe)
    return CheckedRecipe(copy.deepcopy(recipe), school)


@lru_cache(maxsize=1)
def _validator():
    schema = json.loads((CONTRACTS / "recipe.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _check_locked_blocks(recipe):
    """Privacy guard, then face blur, must come first with nothing to tune."""
    blocks = recipe.get("blocks") if isinstance(recipe, dict) else None
    if not isinstance(blocks, list):
        return   # the schema reports it
    head = blocks[:2]
    types = [b.get("type") if isinstance(b, dict) else None for b in head]
    if types != list(policy.LOCKED_BLOCKS) or any(b.get("settings") != {} for b in head):
        raise KozError("SAFETY_LOCKED")


def _only_school_rules_broken(recipe):
    """True if the recipe would pass the schema as a non-school recipe."""
    if not (isinstance(recipe, dict) and isinstance(recipe.get("privacy"), dict)
            and recipe["privacy"].get("school") is True):
        return False
    relaxed = copy.deepcopy(recipe)
    relaxed["privacy"]["school"] = False
    return _validator().is_valid(relaxed)


def _check_order_and_geometry(recipe):
    types = [b["type"] for b in recipe["blocks"]]
    if len(set(types)) != len(types):
        raise KozError("INVALID_RECIPE", "a block appears twice")
    ranks = [policy.BLOCK_ORDER.index(t) for t in types]
    if ranks != sorted(ranks):
        raise KozError("INVALID_RECIPE", "block order")
    for block in recipe["blocks"]:
        settings = block["settings"]
        if block["type"] == "motion_zone":
            left, top, right, bottom = settings["rect"]
            if not (left < right and top < bottom):
                raise KozError("INVALID_RECIPE", "motion_zone rect is empty")
        if block["type"] == "line_counter" and settings["line"][0] == settings["line"][1]:
            raise KozError("INVALID_RECIPE", "line_counter line is a point")
    for action in recipe["actions"]:
        if action["type"] == "alert" and ALERT_NEEDS[action["template"]] not in types:
            raise KozError("INVALID_RECIPE", "alert has no block to come from")


def _check_built(recipe):
    missing = [b["type"] for b in recipe["blocks"] if b["type"] not in policy.BUILT_BLOCKS]
    if recipe["brain"]["type"] not in policy.BUILT_BRAINS:
        missing.append("brain " + recipe["brain"]["type"])
    missing += ["action " + a["type"] for a in recipe["actions"] if a["type"] not in policy.BUILT_ACTIONS]
    if missing:   # these names come from the schema's fixed lists, not free text
        raise KozError("UNSUPPORTED_CAPABILITY", "not built yet: " + ", ".join(missing))


def _no_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate key")
    return dict(pairs)


def _no_constant(_name):
    raise ValueError("NaN or Infinity")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):   # e.g. 1e999 would become Infinity
        raise ValueError("number too large")
    return value


def _all_finite(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_all_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_all_finite(v) for v in value)
    return True


def _depth(value, level=1):
    if isinstance(value, dict):
        return max((_depth(v, level + 1) for v in value.values()), default=level)
    if isinstance(value, list):
        return max((_depth(v, level + 1) for v in value), default=level)
    return level
