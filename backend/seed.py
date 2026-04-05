"""
Run with: python manage.py shell < seed.py
Or:       python seed.py  (from backend/ folder)

Populates the DB with realistic demo data —
3 farm owners, 6 facilities across India, batches, medication logs,
waste logs, and auto-generated alerts with ML scores.
"""

import os
import sys
import django
from datetime import date, timedelta
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from butcher_grid.models import User, Facility, AnimalBatch, MedicationLog, WasteLog, Alert
from butcher_grid.ml_scorer import score_medication, score_waste, compute_facility_risk

# ── Clean slate ───────────────────────────────────────────────────────────────
print("Clearing existing data...")
Alert.objects.all().delete()
WasteLog.objects.all().delete()
MedicationLog.objects.all().delete()
AnimalBatch.objects.all().delete()
Facility.objects.all().delete()
User.objects.filter(is_superuser=False).delete()

# ── Users ─────────────────────────────────────────────────────────────────────
print("Creating users...")

regulator = User.objects.create_user(
    username="fssai_inspector",
    email="inspector@fssai.gov.in",
    password="demo1234",
    role=User.Role.REGULATOR,
    organisation="FSSAI Regional Office",
)

farm_owners = []
owner_data = [
    ("rajan_poultry", "rajan@krishnapoultry.in", "Krishna Poultry Farms Pvt Ltd"),
    ("meera_meats",   "meera@meerameats.in",     "Meera Meats & Livestock"),
    ("anil_agro",     "anil@anilagro.in",         "Anil Agro Industries"),
]
for username, email, org in owner_data:
    u = User.objects.create_user(
        username=username, email=email, password="demo1234",
        role=User.Role.FARM_OWNER, organisation=org,
    )
    farm_owners.append(u)

# ── Facilities ────────────────────────────────────────────────────────────────
print("Creating facilities...")

facilities_data = [
    # (owner_idx, fssai, name, state, capacity, compliance, risk)
    (0, "10016011000001", "Krishna Broiler Farm - Pune",       "Maharashtra",   8000, "compliant",     0.18),
    (0, "10016011000002", "Krishna Layer Farm - Nashik",       "Maharashtra",   5000, "warning",        0.52),
    (1, "21016011000003", "Meera Goat Farm - Coimbatore",      "Tamil Nadu",    1200, "compliant",     0.21),
    (1, "21016011000004", "Meera Slaughterhouse - Chennai",    "Tamil Nadu",    2000, "non_compliant", 0.81),
    (2, "24016011000005", "Anil Cattle Farm - Anand",          "Gujarat",       3000, "warning",        0.47),
    (2, "24016011000006", "Anil Pig Farm - Surat",             "Gujarat",        800, "compliant",     0.14),
]

facilities = []
for oi, fssai, name, state, cap, comp, risk in facilities_data:
    f = Facility.objects.create(
        fssai_license=fssai, name=name, state=state,
        owner=farm_owners[oi], animal_capacity=cap,
        compliance_status=comp, risk_score=risk,
        facility_type="slaughterhouse" if "Slaughterhouse" in name else "farm",
    )
    facilities.append(f)

# ── Animal Batches ────────────────────────────────────────────────────────────
print("Creating batches...")

batches_data = [
    # (facility_idx, code, species, count, days_ago)
    (0, "KPF-CHK-001", "chicken", 2000, 14),
    (0, "KPF-CHK-002", "chicken", 1800, 5),
    (1, "KLF-CHK-003", "chicken", 3000, 21),
    (2, "MGF-GOT-001", "goat",     400, 10),
    (3, "MSH-GOT-002", "goat",     250,  3),
    (3, "MSH-GOT-003", "goat",     300,  8),
    (4, "ACF-CAT-001", "cattle",   180, 30),
    (5, "APF-PIG-001", "pig",      200, 12),
]

batches = []
for fi, code, species, count, days_ago in batches_data:
    b = AnimalBatch.objects.create(
        batch_code=code,
        facility=facilities[fi],
        species=species,
        count=count,
        arrival_date=date.today() - timedelta(days=days_ago),
        status="active",
    )
    batches.append(b)

# ── Medication Logs ───────────────────────────────────────────────────────────
print("Creating medication logs with ML scores...")

meds_data = [
    # (batch_idx, name, type, dosage, withdrawal, days_ago)
    # Clean farm — vaccines only
    (0, "Newcastle Disease Vaccine",   "vaccine",    0.5,  0, 12),
    (0, "Infectious Bronchitis Vaccine","vaccine",   0.5,  0, 10),
    # Warning farm — repeated antibiotics
    (2, "Amoxicillin",                 "antibiotic", 200, 5,  18),
    (2, "Amoxicillin",                 "antibiotic", 250, 5,  14),
    (2, "Ciprofloxacin",               "antibiotic", 150, 7,  10),  # high risk
    (2, "Ciprofloxacin",               "antibiotic", 200, 7,   6),  # high risk
    (2, "Colistin",                    "antibiotic", 300, 3,   3),  # critically important
    # Non-compliant slaughterhouse — banned hormone
    (4, "Oxytetracycline",             "antibiotic", 400, 7,   5),
    (4, "Estradiol",                   "hormone",    50,  21,  2),  # banned
    (5, "Trenbolone",                  "hormone",    80,  28,  1),  # banned
    # Normal cattle farm
    (6, "Ivermectin",                  "vaccine",    10,  0,  25),
    (6, "Oxytetracycline",             "antibiotic", 300, 7,  20),
    # Clean pig farm
    (7, "Porcine Parvovirus Vaccine",  "vaccine",    1,   0,  10),
]

for bi, name, mtype, dosage, withdrawal, days_ago in meds_data:
    batch = batches[bi]

    recent_count = MedicationLog.objects.filter(
        batch=batch, medication_type="antibiotic"
    ).count()

    result = score_medication(
        medication_name=name, medication_type=mtype,
        dosage_mg=dosage, withdrawal_period_days=withdrawal,
        recent_antibiotic_count=recent_count,
    )

    from django.utils import timezone
    log = MedicationLog.objects.create(
        batch=batch, medication_name=name, medication_type=mtype,
        dosage_mg=dosage, withdrawal_period_days=withdrawal,
        risk_score=result["risk_score"], risk_flag=result["risk_flag"],
    )
    # Backdate
    MedicationLog.objects.filter(pk=log.pk).update(
        administered_at=timezone.now() - timedelta(days=days_ago)
    )

    if result["risk_flag"]:
        Alert.objects.create(
            facility=batch.facility,
            alert_type="antibiotic_overuse" if mtype == "antibiotic" else "hormone_flag",
            severity=result["severity"],
            message=f"{name} flagged on {batch.batch_code}. Score: {result['risk_score']}. "
                    f"{'; '.join(result['reasons'])}",
        )

# ── Waste Logs ────────────────────────────────────────────────────────────────
print("Creating waste logs with anomaly scores...")

waste_data = [
    # (facility_idx, type, qty, method, days_ago)
    (0, "solid",    400, "composting",  5),
    (0, "liquid",   200, "biogas",      3),
    (1, "solid",    800, "untreated",   7),   # anomaly
    (1, "liquid",  1200, "sewer",       4),   # anomaly
    (2, "solid",    150, "composting",  6),
    (3, "blood",    300, "untreated",   2),   # anomaly
    (3, "chemical", 120, "untreated",   1),   # serious anomaly
    (4, "solid",    600, "third_party", 10),
    (4, "liquid",   400, "biogas",       8),
    (5, "solid",    200, "composting",   9),
]

from django.utils import timezone as tz
for fi, wtype, qty, method, days_ago in waste_data:
    facility = facilities[fi]

    recent_anomalies = WasteLog.objects.filter(
        facility=facility, is_anomaly=True
    ).count()

    result = score_waste(
        waste_type=wtype, quantity_kg=qty,
        disposal_method=method, recent_anomaly_count=recent_anomalies,
    )

    log = WasteLog.objects.create(
        facility=facility, waste_type=wtype, quantity_kg=qty,
        disposal_method=method,
        anomaly_score=result["anomaly_score"], is_anomaly=result["is_anomaly"],
    )
    WasteLog.objects.filter(pk=log.pk).update(
        logged_at=tz.now() - timedelta(days=days_ago)
    )

    if result["is_anomaly"]:
        Alert.objects.create(
            facility=facility,
            alert_type="waste_anomaly",
            severity=result["severity"],
            message=f"Waste anomaly: {qty}kg of {wtype} via {method}. "
                    f"Score: {result['anomaly_score']}. {'; '.join(result['reasons'])}",
        )

# ── Refresh facility risk scores ──────────────────────────────────────────────
print("Updating facility risk scores...")
for f in facilities:
    flagged = MedicationLog.objects.filter(batch__facility=f, risk_flag=True).count()
    anomalies = WasteLog.objects.filter(facility=f, is_anomaly=True).count()
    open_alerts = Alert.objects.filter(facility=f, is_resolved=False).count()
    score = compute_facility_risk(flagged, anomalies, open_alerts)
    if score >= 0.75:
        comp = "non_compliant"
    elif score >= 0.45:
        comp = "warning"
    else:
        comp = "compliant"
    Facility.objects.filter(pk=f.pk).update(risk_score=score, compliance_status=comp)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n✅ Seed complete!")
print(f"   Users:         {User.objects.count()} (regulator + 3 farm owners)")
print(f"   Facilities:    {Facility.objects.count()}")
print(f"   Batches:       {AnimalBatch.objects.count()}")
print(f"   Medication logs: {MedicationLog.objects.count()} ({MedicationLog.objects.filter(risk_flag=True).count()} flagged)")
print(f"   Waste logs:    {WasteLog.objects.count()} ({WasteLog.objects.filter(is_anomaly=True).count()} anomalies)")
print(f"   Alerts:        {Alert.objects.count()} open")
print()
print("Demo credentials:")
print("  Regulator  → fssai_inspector / demo1234")
print("  Farm owner → rajan_poultry   / demo1234")
print("  Farm owner → meera_meats     / demo1234")
print("  Farm owner → anil_agro       / demo1234")
print()
print("QR codes to scan:")
for b in AnimalBatch.objects.all():
    print(f"  {b.batch_code:20s} → /api/scan/{b.qr_code}/")
