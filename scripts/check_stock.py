from db.session import SessionLocal
from monitor.service import MonitorService

db = SessionLocal()

print(db.bind.url)

try:
    MonitorService().check_all(db)
finally:
    db.close()
