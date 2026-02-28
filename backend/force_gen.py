import os
import sys
# Add backend to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import Deal, GeneratedReport, Analysis
from services.report_generator import ReportGenerator
import json

def fix_all(deal_id):
    db = SessionLocal()
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        print("Deal not found")
        return
        
    analyses_records = db.query(Analysis).filter(Analysis.deal_id == deal_id).all()
    analyses = {a.analysis_type: json.loads(a.results) for a in analyses_records if a.results}
    
    deal_data = {
        "id": deal.id,
        "name": deal.name,
        "target_company": deal.target_company,
        "industry": deal.industry,
        "deal_size": deal.deal_size
    }
    
    narrative = {}
    gen = ReportGenerator()
    report_types = ["iar", "dcf", "red_flag", "qoe", "nwc", "executive_summary"]
    
    for rt in report_types:
        try:
            print(f"Generating {rt}...")
            path = gen.generate(rt, deal_data, analyses, narrative)
            print(f"Generated {rt} at: {path}")
            
            # Update DB entry if exists
            report = db.query(GeneratedReport).filter(
                GeneratedReport.deal_id == deal_id,
                GeneratedReport.report_type == rt
            ).first()
            if report:
                report.file_path = path
                db.commit()
        except Exception as e:
            print(f"Failed {rt}: {e}")
            import traceback
            traceback.print_exc()
            
    db.close()

if __name__ == "__main__":
    fix_all(1)
