"""Violation weights and risk levels. Tune these to change how strict proctoring is."""

WEIGHTS = {
    "prohibited_object": 20,
    "multiple_faces": 15,
    "no_face": 8,
    "tab_switch": 5,
    "fullscreen_exit": 5,
    "copy_paste": 3,
}

CLIENT_EVENTS = {"tab_switch", "fullscreen_exit", "copy_paste"}  # events the browser may report


def risk_level(score: int) -> str:
    if score >= 50:
        return "high"
    if score >= 20:
        return "medium"
    return "low"
