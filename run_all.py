"""Reproduce everything: python run_all.py   (about 5 minutes)
Builds the master dataset, executes the four notebooks, writes the data dictionary and the dashboard."""
import subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
env = dict(os.environ, PYTHONUTF8="1", MPLBACKEND="module://matplotlib_inline.backend_inline")
NB = ["01_data_audit", "02_build_master", "03_eda", "04_index_cluster_ml"]

for n in NB:
    out = ROOT / "notebooks" / f"{n}.ipynb"
    subprocess.run([sys.executable, "-m", "jupytext", "--to", "ipynb", str(ROOT / "src" / f"{n}.py"), "-o", str(out), "-q"], check=True, env=env)
    subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
                    "--ExecutePreprocessor.timeout=1800", str(out)], check=True, env=env, cwd=ROOT / "notebooks")
for s in ["05_data_dictionary", "06_build_dashboard"]:
    subprocess.run([sys.executable, str(ROOT / "src" / f"{s}.py")], check=True, env=env)
print("done -> final/RuralReach_Master.csv, docs/index.html")
