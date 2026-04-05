"""
Rule-based risk scorer — acts as the AI brain for the demo.
No external ML service needed. Scores are deterministic and explainable,
which is actually better for a hackathon demo than a black-box model.
"""


# Antibiotics known to cause high AMR risk
HIGH_RISK_ANTIBIOTICS = {
    "colistin", "carbapenem", "vancomycin", "linezolid",
    "ciprofloxacin", "azithromycin", "ceftriaxone",
}

# Hormones banned in Indian livestock
BANNED_HORMONES = {
    "estradiol", "testosterone", "progesterone",
    "zeranol", "melengestrol", "trenbolone",
}

RISKY_DISPOSAL = {"untreated", "sewer"}


def score_medication(medication_name: str, medication_type: str,
                     dosage_mg: float, withdrawal_period_days: int,
                     recent_antibiotic_count: int = 0) -> dict:
    """
    Returns a risk_score (0.0–1.0) and a human-readable reason.
    Called synchronously in the view — no Celery needed.
    """
    score = 0.0
    reasons = []

    name_lower = medication_name.lower()

    if medication_type == "antibiotic":
        # Base score for any antibiotic use
        score += 0.2
        reasons.append("Antibiotic administered")

        # High-risk antibiotic family
        if any(h in name_lower for h in HIGH_RISK_ANTIBIOTICS):
            score += 0.35
            reasons.append(f"{medication_name} is a critically important antibiotic (WHO list)")

        # Overuse — too many in recent window
        if recent_antibiotic_count >= 5:
            score += 0.25
            reasons.append(f"{recent_antibiotic_count} antibiotic logs in last 7 days")
        elif recent_antibiotic_count >= 3:
            score += 0.10
            reasons.append(f"{recent_antibiotic_count} antibiotic logs in last 7 days")

        # High dosage relative to withdrawal period
        if dosage_mg > 500 and withdrawal_period_days < 7:
            score += 0.20
            reasons.append("High dosage with short withdrawal period")

    elif medication_type == "hormone":
        score += 0.30
        reasons.append("Hormone administered")

        if any(b in name_lower for b in BANNED_HORMONES):
            score += 0.55
            reasons.append(f"{medication_name} is banned under FSSAI/PFA regulations")

    elif medication_type == "vaccine":
        score += 0.05
        reasons.append("Vaccine — low risk")

    score = round(min(score, 1.0), 3)
    risk_flag = score >= 0.50

    return {
        "risk_score": score,
        "risk_flag": risk_flag,
        "severity": _severity(score),
        "reasons": reasons,
    }


def score_waste(waste_type: str, quantity_kg: float,
                disposal_method: str, recent_anomaly_count: int = 0) -> dict:
    score = 0.0
    reasons = []

    if disposal_method in RISKY_DISPOSAL:
        score += 0.45
        reasons.append(f"Disposal method '{disposal_method}' risks environmental contamination")

    if waste_type == "chemical":
        score += 0.30
        reasons.append("Chemical waste requires certified disposal")
    elif waste_type == "blood":
        score += 0.15
        reasons.append("Blood waste — pathogen risk if untreated")

    if quantity_kg > 1000:
        score += 0.20
        reasons.append(f"Large volume: {quantity_kg}kg exceeds normal threshold")
    elif quantity_kg > 500:
        score += 0.10
        reasons.append(f"Above-average volume: {quantity_kg}kg")

    if recent_anomaly_count >= 2:
        score += 0.15
        reasons.append(f"Repeated anomalies: {recent_anomaly_count} in recent logs")

    score = round(min(score, 1.0), 3)
    is_anomaly = score >= 0.50

    return {
        "anomaly_score": score,
        "is_anomaly": is_anomaly,
        "severity": _severity(score),
        "reasons": reasons,
    }


def compute_facility_risk(flagged_meds: int, waste_anomalies: int,
                          open_alerts: int) -> float:
    """Weighted composite score used for facility-level risk."""
    med_score = min(flagged_meds / 5.0, 1.0) * 0.45
    waste_score = min(waste_anomalies / 3.0, 1.0) * 0.35
    alert_score = min(open_alerts / 3.0, 1.0) * 0.20
    return round(med_score + waste_score + alert_score, 3)


def _severity(score: float) -> str:
    if score >= 0.80:
        return "critical"
    if score >= 0.60:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"
