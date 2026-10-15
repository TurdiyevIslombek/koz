"""The privacy guard's scene check: the decision rule, and the real Places365 model with OpenCV 5."""
import numpy as np
import pytest

from koz import MODELS, policy
from koz.capture import FileCamera
from koz.errors import KozError
from koz.privacy import FAILED, PrivacyResult
from koz.scene import CLASSES, MODEL_PATH, PlacesSceneChecker, decide

KITCHEN, CLASSROOM, CATACOMB, STAIRCASE = 203, 92, 85, 317   # ordinary places, none private
CORRIDOR, LOBBY, HOME_OFFICE, ENTRANCE_HALL = 106, 217, 176, 134


def probs(**weights):
    """365 probabilities: the given {index: weight} share 1 - rest, the rest is spread evenly."""
    p = np.zeros(CLASSES)
    chosen = {int(k.lstrip("i")): v for k, v in weights.items()}
    rest = 1 - sum(chosen.values())
    others = [i for i in range(CLASSES) if i not in chosen]
    p[others] = rest / len(others)
    for i, v in chosen.items():
        p[i] = v
    return p


def test_private_names_match_the_category_list():
    names = [line.split()[0] for line in (MODELS / "categories_places365.txt").read_text().splitlines()]
    assert len(names) == CLASSES
    for scenes in policy.PRIVATE_SCENES.values():
        for index, name in scenes:
            assert names[index] == "/" + name[0] + "/" + name
    assert sum(len(s) for s in policy.PRIVATE_SCENES.values()) == 16


@pytest.mark.parametrize("weights, expected", [
    ({"i45": 0.6}, PrivacyResult("blocked", "PRIVATE_BATHROOM")),         # bathroom on top
    ({"i303": 0.3}, PrivacyResult("blocked", "PRIVATE_BATHROOM")),        # shower on top
    ({"i52": 0.5}, PrivacyResult("blocked", "PRIVATE_BEDROOM")),
    ({"i219": 0.5}, PrivacyResult("blocked", "PRIVATE_CHANGING_ROOM")),
    # A kitchen on top, but bedrooms together are likely enough to stop.
    ({f"i{KITCHEN}": 0.5, "i52": 0.08, "i51": 0.04, "i182": 0.04}, PrivacyResult("blocked", "PRIVATE_BEDROOM")),
    ({f"i{KITCHEN}": 0.12}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),   # nothing is clear
    ({f"i{CLASSROOM}": 0.7}, PrivacyResult("approved")),
    # Allowlist (after live test #1): a confident place that isn't on the list is not approved.
    ({f"i{CATACOMB}": 0.6}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),   # the live bug
    ({f"i{KITCHEN}": 0.7}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),    # home rooms aren't listed
    ({f"i{CLASSROOM}": 0.25}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),  # allowed, but not sure enough
    # A private room anywhere in the top 5 above 0.10 stops it, even under a confident classroom.
    ({f"i{CLASSROOM}": 0.7, "i52": 0.12}, PrivacyResult("blocked", "PRIVATE_BEDROOM")),
])
def test_strict_decision_rule(weights, expected):
    assert decide(probs(**weights), strict=True) == expected


@pytest.mark.parametrize("weights, expected", [
    # Removed after the security review: private rooms get mistaken for these.
    ({f"i{STAIRCASE}": 0.7}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),
    ({f"i{ENTRANCE_HALL}": 0.7}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),
    ({f"i{HOME_OFFICE}": 0.7}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),
    # Corridors and lobbies must be at least 0.50 sure.
    ({f"i{CORRIDOR}": 0.45}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),
    ({f"i{LOBBY}": 0.45}, PrivacyResult("unknown", "PRIVACY_UNCERTAIN")),
    ({f"i{CORRIDOR}": 0.55}, PrivacyResult("approved")),
])
def test_strict_cautious_and_removed_places(weights, expected):
    assert decide(probs(**weights), strict=True) == expected


@pytest.mark.parametrize("weights, expected", [
    ({f"i{KITCHEN}": 0.7}, PrivacyResult("approved")),            # not on the allowlist, but vouched for
    ({f"i{CATACOMB}": 0.6}, PrivacyResult("approved")),
    ({f"i{KITCHEN}": 0.12}, PrivacyResult("approved")),           # unclear is fine too
    # Default mode (live test #3): only a confident room check stops it (the object check
    # in koz/privacy.py does the rest): a desk in a bedroom may look a bit like a bedroom.
    ({f"i{KITCHEN}": 0.7, "i52": 0.12}, PrivacyResult("approved")),
    ({f"i{KITCHEN}": 0.5, "i52": 0.08, "i51": 0.04, "i182": 0.04}, PrivacyResult("approved")),
    ({"i52": 0.30}, PrivacyResult("approved")),                                         # unsure bedroom
    ({"i45": 0.6}, PrivacyResult("blocked", "PRIVATE_BATHROOM")),                       # top guess >= 0.50
    ({f"i{KITCHEN}": 0.3, "i52": 0.2, "i51": 0.12, "i182": 0.1}, PrivacyResult("blocked", "PRIVATE_BEDROOM")),  # >= 0.40 together
])
def test_default_mode_stops_only_on_a_confident_private_room(weights, expected):
    assert decide(probs(**weights)) == expected


@pytest.mark.parametrize("bad", [np.ones(10) / 10, np.full(CLASSES, np.nan), np.full(CLASSES, 2 / CLASSES),
                                 np.r_[-0.5, np.full(CLASSES - 1, 1.5 / (CLASSES - 1))]])
def test_malformed_output_is_a_failed_check(bad):
    assert decide(bad) == FAILED


def test_category_names_used_by_the_guard_exist():
    from koz.scene import NAMES
    assert (NAMES[CATACOMB], NAMES[STAIRCASE], NAMES[KITCHEN], NAMES[CLASSROOM]) == \
        ("catacomb", "staircase", "kitchen", "classroom")
    assert (NAMES[CORRIDOR], NAMES[LOBBY], NAMES[HOME_OFFICE], NAMES[ENTRANCE_HALL]) == \
        ("corridor", "lobby", "home_office", "entrance_hall")
    assert set(policy.CAUTIOUS_SCENES) <= set(policy.ALLOWED_SCENES)
    assert not {"staircase", "entrance_hall", "home_office"} & set(policy.ALLOWED_SCENES)
    assert all(name in NAMES for name in policy.ALLOWED_SCENES)
    private = {name for scenes in policy.PRIVATE_SCENES.values() for _, name in scenes}
    assert not private & set(policy.ALLOWED_SCENES)


def test_dark_flat_or_hidden_frames_cannot_be_judged():
    from koz.scene import too_dark_or_flat
    rng = np.random.default_rng(1)
    bright = rng.integers(40, 220, (240, 320, 3), dtype=np.uint8)          # a lit, detailed frame
    assert not too_dark_or_flat(bright)
    assert too_dark_or_flat((bright * 0.12).astype(np.uint8))              # a camera's first frames
    assert too_dark_or_flat(np.full((240, 320, 3), 128, np.uint8))         # flat grey, e.g. a covered lens
    masked = bright.copy()
    masked[:, 160:] = 0                                                    # half blacked out by the mask
    assert not too_dark_or_flat(masked)                                    # judged on the visible half only
    masked[:, 20:] = 0
    assert too_dark_or_flat(masked)                                        # almost nothing left to judge


def test_missing_or_changed_model_is_refused(tmp_path):
    fake = tmp_path / "places365_resnet18.onnx"
    fake.write_bytes(b"not the model")
    for path in (tmp_path / "missing.onnx", fake):
        with pytest.raises(KozError) as caught:
            PlacesSceneChecker(path)
        assert caught.value.code == "PRIVACY_UNAVAILABLE"


needs_model = pytest.mark.skipif(not MODEL_PATH.exists(), reason="run scripts/fetch_models.py first")


@needs_model
def test_real_model_gives_valid_answers_on_recorded_video(test_video):
    """OpenCV 5 runs the pinned model and every answer is well formed. Whether it
    recognises real bathrooms can only be measured in the privacy trials."""
    checker = PlacesSceneChecker()
    with FileCamera(test_video) as camera:
        while (frame := camera.read()) is not None:
            p = checker.probabilities(frame.image)
            assert p.shape == (CLASSES,) and abs(p.sum() - 1) < 1e-3
            assert checker.check(frame.image).state in ("approved", "blocked", "unknown")
