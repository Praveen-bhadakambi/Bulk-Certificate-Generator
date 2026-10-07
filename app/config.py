from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CERTIFICATE_DIR = DATA_DIR / "certificates"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'certificates.db'}"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)
