"""The adjust step: when a check fails, propose ONE setting change from what OpenCV measured.

This runs on this computer and looks at the (masked, face-blurred) frames of the round that
just failed; nothing it looks at leaves the computer (CLAUDE.md rule 9: the planner only
gets text, recipes and numbers). Contract section 7: an adjustment changes exactly one of
the listed settings and nothing else (no new blocks, no geometry, no safety settings).

Colour finder, target not found:
  1. Look for the most common strongly coloured hue within HUE_SEARCH of the asked colour
     (so "red" can become orange-red, but never green). If there is one, move hue_center there.
  2. Otherwise, if the colour may just be pale, lower saturation_min by 40 (not below 50).
People counter: nothing to adjust from the numbers alone (no change; the loop stops).

Fly-brain car, ball seen but not kept in the middle (target_centered): the brain turns too weakly.
  1. turn_gain x 1.5 (stronger looming on the eye opposite the ball), up to 2.0;
  2. at 2.0, a narrower deadband (it starts turning sooner), down to 0.02."""
import cv2
import numpy as np

HUE_SEARCH = 25          # how far from the asked colour the tuner may look (OpenCV hue, 0..179)
MIN_SHARE = 0.001        # the hue must cover at least this share of the pixels looked at


def dominant_hue(frames, centre, saturation_min, value_min):
    """The most common hue near `centre` among colourful pixels, or None if there is none."""
    counts = np.zeros(180)
    total = 0
    for frame in frames:
        hue, sat, val = cv2.split(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV))
        h = hue[(sat >= saturation_min) & (val >= value_min)].astype(np.int16)
        distance = np.minimum(np.abs(h - centre), 180 - np.abs(h - centre))
        counts += np.bincount(h[distance <= HUE_SEARCH], minlength=180)
        total += hue.size
    if not total:
        return None
    smooth = sum(np.roll(counts, k) for k in (-2, -1, 0, 1, 2))   # around the hue circle
    peak = int(np.argmax(smooth))
    return peak if smooth[peak] >= MIN_SHARE * total else None


def propose(recipe, check, frames):
    """A SettingChange {"setting", "before", "after"} for the failed check, or None."""
    if check == "target_centered" and recipe["brain"]["type"] == "flybrain":
        return _steer_harder(recipe["brain"]["settings"])
    finder = next((b for b in recipe["blocks"] if b["type"] == "color_finder"), None)
    if check != "target_visible" or finder is None or not frames:
        return None
    s = finder["settings"]
    hue = dominant_hue(frames, s["hue_center"], s["saturation_min"], s["value_min"])
    if hue is not None:
        off = min(abs(hue - s["hue_center"]), 180 - abs(hue - s["hue_center"]))
        if off > s["hue_half_width"] / 2:
            return {"setting": "color_finder.hue_center", "before": s["hue_center"], "after": hue}
    if s["saturation_min"] - 40 >= 50:
        return {"setting": "color_finder.saturation_min", "before": s["saturation_min"],
                "after": s["saturation_min"] - 40}
    return None


def apply(recipe, change):
    """A copy of `recipe` with the one change made."""
    block, name = change["setting"].split(".")
    new = {**recipe, "blocks": [dict(b, settings=dict(b["settings"])) for b in recipe["blocks"]]}
    if block == "brain":
        new["brain"] = dict(recipe["brain"], settings={**recipe["brain"]["settings"], name: change["after"]})
        return new
    for b in new["blocks"]:
        if b["type"] == block:
            b["settings"][name] = change["after"]
    return new


def _steer_harder(settings):
    gain, band = settings["turn_gain"], settings["deadband"]
    if gain < 2.0:
        return {"setting": "brain.turn_gain", "before": gain, "after": min(2.0, round(gain * 1.5, 2))}
    if band > 0.02:
        return {"setting": "brain.deadband", "before": band, "after": max(0.02, round(band - 0.03, 2))}
    return None
