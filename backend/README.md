# Butcher Grid — Backend

## Setup (5 minutes, no Docker needed)

### 1. Create virtual environment
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run migrations
```bash
python manage.py migrate
```

### 4. Seed demo data
```bash
python seed.py
```

### 5. Start the server
```bash
python manage.py runserver
```

Server runs at http://localhost:8000

---

## Demo credentials
| Role | Username | Password |
|------|----------|----------|
| Regulator | fssai_inspector | demo1234 |
| Farm Owner | rajan_poultry | demo1234 |
| Farm Owner | meera_meats | demo1234 |
| Farm Owner | anil_agro | demo1234 |

---

## Key endpoints

### Auth
- `POST /api/auth/token/` — get JWT token `{"username": "...", "password": "..."}`
- `POST /api/auth/register/` — register new user

### Farm owner
- `GET/POST /api/facilities/` — list or create facilities
- `GET/POST /api/batches/` — list or create animal batches
- `GET/POST /api/medications/` — log medication (AI scores instantly on POST)
- `GET/POST /api/waste/` — log waste (AI scores instantly on POST)
- `GET /api/alerts/` — view alerts

### Regulator
- `GET /api/dashboard/` — national overview stats
- `GET /api/alerts/` — all alerts across all facilities
- `POST /api/alerts/<id>/resolve/` — resolve an alert

### Consumer (no login needed)
- `GET /api/scan/<qr_code>/` — scan a batch QR code

---

## How the AI scoring works
No external ML service. Scoring runs synchronously in `ml_scorer.py`:
- Checks WHO critically important antibiotic list
- Checks FSSAI/PFA banned hormone list
- Weights recent overuse, dosage vs withdrawal period
- Returns risk_score (0.0–1.0) + human-readable reasons
- Auto-creates alerts and updates facility risk score
