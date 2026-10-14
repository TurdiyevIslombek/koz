"""The privacy guard's scene check: the decision rule, and the real Places365 model with OpenCV 5."""
import numpy as np
import pytest

from koz import MODELS, policy
from koz.capture import FileCamera
from koz.errors import KozError
from koz.privacy import FAILED, PrivacyResult
from koz.scene import CLASSES, MODEL_PATH, PlacesSceneChecker, decide

KITCHEN, CLASSROOM = 203, 92   # two ordinary places, for the "not private" cases


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
])
def test_decision_rule(weights, expected):
    assert decide(probs(**weights)) == expected


@pytest.mark.parametrize("bad", [np.ones(10) / 10, np.full(CLASSES, np.nan), np.full(CLASSES, 2 / CLASSES),
                                 np.r_[-0.5, np.full(CLASSES - 1, 1.5 / (CLASSES - 1))]])
def test_malformed_output_is_a_failed_check(bad):
    assert decide(bad) == FAILED


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
