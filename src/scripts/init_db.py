import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
from app.db.manage import init_db

# python3 src/scripts/init_db.py

asyncio.run(init_db())
print("Tables created!")