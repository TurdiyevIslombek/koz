"""One readable line per event, for the terminal: the agent's chain of observation -> decision
-> new setting -> result, as it happens. It only formats the contract events; nothing new."""
from ..messages import message


def _settings(recipe):
    parts = []
    for block in recipe["blocks"][2:]:
        s = block["settings"]
        if block["type"] == "color_finder":
            parts.append(f"hue {s['hue_center']}±{s['hue_half_width']}, saturation ≥ {s['saturation_min']}")
        elif block["type"] == "person_detector":
            parts.append(f"person confidence ≥ {s['min_confidence']}")
        elif block["type"] == "line_counter":
            parts.append(f"line {s['line']}")
    return "; ".join(parts) + ("; school mode" if recipe["privacy"]["school"] else "")


def _count(c):
    return "-" if c is None else str(c["value"]) if c["state"] == "known" else "?"


class ChainLog:
    """Call it with each event; it returns a line to print, or None (unchanged statuses)."""

    def __init__(self, language="en"):
        self.language, self._state = language, None

    def __call__(self, event):
        kind, data, seq, rev = event["type"], event["data"], event["seq"], event["revision"]
        if kind == "status":
            if data["state"] == self._state:
                return None
            self._state = data["state"]
            return f"#{seq:<4} status    {data['state']}" + (f" (revision {rev})" if rev else "")
        if kind == "recipe":
            cause = f", because of decision #{data['caused_by']}" if data["caused_by"] else ""
            return f"#{seq:<4} recipe    revision {rev} from the {data['origin']}{cause}: {_settings(data['recipe'])}"
        if kind == "observation":
            what = (f"target {data['target']}" if data["target"] is not None
                    else f"people {_count(data['occupancy'])}, in {_count(data['entered'])}, out {_count(data['exited'])}")
            reason = f" ({data['unknown_reason']})" if data["unknown_reason"] else ""
            return f"#{seq:<4} observe   round {data['round'] or '-'} revision {rev}: privacy {data['privacy']}, {what}{reason}"
        if kind == "decision":
            change = data["change"]
            how = f": {change['setting']} {change['before']} -> {change['after']}" if change else ""
            code = f" [{data['code']}]" if data["code"] else ""
            return (f"#{seq:<4} decide    round {data['round']}: {data['check']} {data['result']} "
                    f"(from #{', #'.join(map(str, data['evidence_seq']))}) -> {data['next']}{how}{code}")
        if kind == "fault":
            return f"#{seq:<4} stopped   {data['code']}: {message(data['code'], self.language)}"
        if kind == "command_result":
            return f"#{seq:<4} command   {data['result']}" + (f" [{data['code']}]" if data["code"] else "")
        return f"#{seq:<4} {kind}"
