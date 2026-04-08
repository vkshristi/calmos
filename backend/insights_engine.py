def safe_avg(values):
    return sum(values) / len(values) if values else None


def normalize(value, min_v, max_v):
    return (value - min_v) / (max_v - min_v) if value is not None else None

def sleep_vs_flow(records):
    pairs = [
        (r["sleep"], r["flow"])
        for r in records
        if r["sleep"] is not None and r["flow"] is not None
    ]

    if len(pairs) < 2:
        return None

    high_sleep = [f for s, f in pairs if s >= 7]
    low_sleep = [f for s, f in pairs if s < 7]

    if not high_sleep or not low_sleep:
        return None

    return round(safe_avg(high_sleep) - safe_avg(low_sleep), 2)

def stress_vs_focus(records):
    pairs = [
        (r["stress"], r["focus"])
        for r in records
        if r["stress"] is not None and r["focus"] is not None
    ]

    if len(pairs) < 2:
        return None

    high_stress = [f for s, f in pairs if s >= 4]
    low_stress = [f for s, f in pairs if s <= 2]

    if not high_stress or not low_stress:
        return None

    return round(safe_avg(low_stress) - safe_avg(high_stress), 2)

def context_switch_penalty(records):
    pairs = [
        (r["sessions"], r["avg_flow"])
        for r in records
        if r["sessions"] is not None and r["avg_flow"] is not None
    ]

    if len(pairs) < 2:
        return None

    high_switch = [f for s, f in pairs if s >= 4]
    low_switch = [f for s, f in pairs if s <= 2]

    if not high_switch or not low_switch:
        return None

    return round(safe_avg(low_switch) - safe_avg(high_switch), 2)

def burnout_risk(latest):
    if not latest:
        return None

    score = 0

    # High stress
    if latest["stress"] >= 4:
        score += 30

    # Low sleep
    if latest["sleep"] < 6:
        score += 25

    # Low flow
    if latest["flow"] < 50:
        score += 25

    # Too much work
    if latest["focus"] > 120:
        score += 20

    return min(score, 100)

def generate_insights(sleep_corr, stress_corr, switch_penalty, burnout):
    insights = []

    if sleep_corr is not None:
        if sleep_corr > 5:
            insights.append("You perform significantly better when well-rested.")
        elif sleep_corr < -5:
            insights.append("Unexpected: more sleep is not improving your flow.")

    if stress_corr is not None:
        if stress_corr > 5:
            insights.append("Lower stress strongly improves your focus.")
        elif stress_corr < -5:
            insights.append("Your focus remains stable even under stress.")

    if switch_penalty is not None:
        if switch_penalty > 5:
            insights.append("Frequent context switching is hurting your flow.")

    if burnout is not None:
        if burnout >= 70:
            insights.append("High burnout risk — reduce workload and recover.")
        elif burnout >= 40:
            insights.append("Moderate burnout risk — consider lighter tasks.")

    return insights
