import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
from app.db.base import init_db

asyncio.run(init_db())
print("Tables created!")