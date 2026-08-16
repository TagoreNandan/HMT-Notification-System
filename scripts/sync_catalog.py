from db.session import SessionLocal, init_db
from catalog.sync import CatalogSyncService

init_db()  # <-- Create any missing tables

db = SessionLocal()

try:
    stats = CatalogSyncService().sync(db)
    print(stats)
finally:
    db.close()
