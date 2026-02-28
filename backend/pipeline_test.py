from database import SessionLocal
from routers.analysis import run_analysis_pipeline
import sys

# Run normally, print stdout/stderr
run_analysis_pipeline(1)
print("Finished running pipeline.")
