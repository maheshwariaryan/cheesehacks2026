from database import SessionLocal
from routers.analysis import run_analysis_pipeline

run_analysis_pipeline(1)
