def normalize_mood(mood: int) -> float:
    return (mood - 1) / 4


def normalize_stress(stress: int) -> float:
    return 1 - ((stress - 1) / 4)


def normalize_sleep(hours: int) -> float:
    hours = min(hours, 8)
    return hours / 8


def normalize_exercise(exercise: bool) -> float:
    return 1.0 if exercise else 0.0


def normalize_focus_minutes(minutes: int) -> float:
    minutes = min(minutes, 120)
    return minutes / 120


def normalize_avg_flow(avg_flow: float | None) -> float:
    if avg_flow is None:
        return 0.0
    return (avg_flow - 1) / 4


def compute_flow_score(wellness, focus):
    # If no wellness logged → no score
    if not wellness:
        return None

    mood = wellness.get("mood")
    sleep = wellness.get("sleep_hours")
    stress = wellness.get("stress")
    exercise = wellness.get("exercise")

    total_minutes = focus.get("total_minutes", 0)
    avg_flow = focus.get("average_flow")

    # Normalize to 0–100 rough scale
    mood_score = (mood / 5) * 20
    sleep_score = min(sleep / 8, 1) * 20
    stress_score = ((5 - stress) / 5) * 20
    exercise_score = 10 if exercise else 0
    focus_score = min(total_minutes / 120, 1) * 15

    flow_rating_score = (avg_flow / 5) * 15 if avg_flow else 0

    total = (
        mood_score
        + sleep_score
        + stress_score
        + exercise_score
        + focus_score
        + flow_rating_score
    )

    return round(total, 1)