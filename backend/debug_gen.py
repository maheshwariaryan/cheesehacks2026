import os
import sys
# Add backend to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import Deal, GeneratedReport, Analysis
from services.report_generator import ReportGenerator
import json

def test_gen():
    db = SessionLocal()
    deal = db.query(Deal).filter(Deal.id == 1).first()
    analyses_records = db.query(Analysis).filter(Analysis.deal_id == 1).all()
    analyses = {a.analysis_type: json.loads(a.results) for a in analyses_records if a.results}
    
    # Mock narrative
    narrative = {}
    
    gen = ReportGenerator()
    try:
        path = gen.generate("iar", deal.__dict__, analyses, narrative)
        print(f"Generated at: {path}")
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_gen()
