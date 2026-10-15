"""The local preview window: what Ko'z itself sees (the allowed area, faces blurred), with the
target ring or people boxes, the status line, the privacy check line, and a big red banner when
it stops. Used by scripts/live_demo.py, scripts/agent_demo.py and koz/server.py --window.

It only draws on screen (cv2.imshow): nothing here saves or sends a frame (CLAUDE.md rule 8)."""
import cv2
import numpy as np

WINDOW = "Ko'z live demo (q to quit)"
GREEN, AMBER, RED, WHITE = (60, 180, 75), (0, 170, 255), (60, 60, 230), (255, 255, 255)
BANNER_RED = (30, 30, 190)
FONT = cv2.FONT_HERSHEY_SIMPLEX   # OpenCV's built-in fonts are ASCII only, so no long dashes
ROOM_GUESS = {"PRIVATE_BATHROOM": "bathroom", "PRIVATE_TOILET": "toilet",
              "PRIVATE_BEDROOM": "bedroom", "PRIVATE_CHANGING_ROOM": "changing room"}


def count_text(count):
    return "-" if count is None else "?" if count["state"] == "unknown" else str(count["value"])


def check_line(runner):
    """The privacy guard's latest check in one line (room guesses, objects seen, result)."""
    return getattr(runner.guard, "line", "check: -")


def draw(runner, latest, messages, fps, line, note=None):
    """The window picture for the latest frame. `latest` holds the newest event data by type;
    `note` is one more line to show (e.g. who planned the job)."""
    width, height = runner.size
    view = runner.preview.copy() if runner.preview is not None else np.zeros((height, width, 3), np.uint8)
    for person in runner.local_results.get("person_detector", ()):
        x0, y0, x1, y1 = (int(v) for v in person.box)
        cv2.rectangle(view, (x0, y0), (x1, y1), AMBER, 2)
    if line is not None:
        a, b = (int(line[0] * width), int(line[1] * height)), (int(line[2] * width), int(line[3] * height))
        cv2.line(view, a, b, WHITE, 2)
        cv2.putText(view, "B", b, cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
    target = runner.local_results.get("color_finder")
    if target is not None and target.x is not None:
        centre = (int(target.x * width), int(target.y * height))
        radius = max(8, int((target.area_ratio * width * height / np.pi) ** 0.5))
        cv2.circle(view, centre, radius, GREEN, 3)
        cv2.putText(view, target.label, (centre[0] + radius + 6, centre[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)

    status = latest.get("status", {})
    observation = latest.get("observation", {})
    fault = latest.get("fault")
    state = status.get("state", "starting")
    colour = GREEN if state == "running" else AMBER if state in ("checking", "evaluating") else RED
    privacy = status.get("privacy", "-")
    if runner.strict and privacy == "approved":
        privacy = "approved (strict)"
    if line is not None:
        job = (f"people: {count_text(observation.get('occupancy'))}   in: {count_text(observation.get('entered'))}"
               f"   out: {count_text(observation.get('exited'))}")
    else:
        job = f"target: {observation.get('target', '-')}"
    lines = [f"state: {state}   privacy: {privacy}   {job}   {fps:4.1f} fps", check_line(runner)]
    reason = fault["code"] if fault else observation.get("unknown_reason")
    if reason:
        lines.append(f"{reason}: {messages.get(reason, '')}")
    if note:
        lines.append(note)
    if runner.strict:
        lines.append("STRICT MODE: runs only in listed public places (classroom, shop, office...)")
    cv2.rectangle(view, (0, 0), (width, 28 * len(lines) + 8), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        tint = colour if i == 0 else AMBER if line.startswith("STRICT MODE") else WHITE
        cv2.putText(view, line, (10, 24 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6 if i < 2 else 0.45, tint, 1)
    if fault:
        last = getattr(runner.guard, "last_result", None)
        title, banner = stop_banner(fault["code"], messages, runner.strict, getattr(last, "seen", None))
        draw_banner(view, title, banner, check_line(runner))
    return view


OBJECT_STOP = {"bed": "a bed is in view.", "toilet": "a toilet is in view.",
               "sink": "a sink, in what looks like a bathroom."}


def stop_banner(code, messages, strict, seen=None):
    """What the big banner says when Ko'z stops: (title, lines). `seen` is the object the
    privacy guard saw (bed, toilet, sink), if that is what stopped it. Short by default;
    only strict mode talks about allowed places."""
    if seen in OBJECT_STOP and code in ROOM_GUESS:
        return "STOPPED", [OBJECT_STOP[seen]]
    if code in ROOM_GUESS:
        room = ROOM_GUESS[code]
        if strict:
            return "STOPPED", [f"this room isn't allowed ({room}?)", "Private rooms always stop Ko'z."]
        return "STOPPED", [f"this looks like a {room}."]
    if code == "PRIVACY_UNCERTAIN":
        if strict:
            return "STOPPED", ["not a listed public place (strict mode)",
                               "Too dark, or not a classroom, shop or office."]
        return "STOPPED", ["camera is covered or too dark."]   # by default only darkness makes it unsure
    return "STOPPED", [messages.get(code, code), f"({code})"]


def startup_banner(code, messages, camera_problem):
    """What the banner says when Ko'z can't start at all: (title, lines)."""
    if camera_problem:
        return "CAMERA NOT ALLOWED", ["macOS didn't let this app use the camera.",
                                      "Allow Terminal in System Settings > Privacy & Security > Camera,",
                                      "then double-click the demo again."]
    return "KO'Z DID NOT START", [messages.get(code, code), f"({code})"]


def put_centred(view, text, y, scale, thickness, colour):
    """Write text centred at height y, shrinking it until it fits the width."""
    while scale > 0.3 and cv2.getTextSize(text, FONT, scale, thickness)[0][0] > view.shape[1] - 30:
        scale -= 0.05
    width = cv2.getTextSize(text, FONT, scale, thickness)[0][0]
    cv2.putText(view, text, ((view.shape[1] - width) // 2, y), FONT, scale, colour, thickness, cv2.LINE_AA)


def draw_banner(view, title, lines, check_line=None):
    """A full-width red band across the middle of the window, with the last check under it."""
    height = view.shape[0]
    top = height // 2 - 70
    bottom = top + 90 + 34 * len(lines) + (26 if check_line else 0)
    cv2.rectangle(view, (0, top), (view.shape[1], bottom), BANNER_RED, -1)
    put_centred(view, title, top + 60, 1.8, 4, WHITE)
    for i, text in enumerate(lines):
        put_centred(view, text, top + 100 + 34 * i, 0.75, 2, WHITE)
    if check_line:
        put_centred(view, check_line, bottom - 12, 0.45, 1, WHITE)
    return view


def quit_pressed(wait_ms, window=None):
    """q, Esc, or the window's close button."""
    key = cv2.waitKey(wait_ms) & 0xFF
    return key in (ord("q"), 27) or cv2.getWindowProperty(window or WINDOW, cv2.WND_PROP_VISIBLE) < 1

