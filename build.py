"""Build the static site into dist/ for Cloudflare Pages.

dist/ = web/ + py/utils.zip (our Python code) + wheels/ (pure-Python libraries Pyodide lacks).
Run: python build.py   then preview: python -m http.server -d dist
"""
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
# Pure-Python wheels served from our own origin (Pyodide's own index provides the rest).
WHEELS = ["openpyxl==3.1.5", "et-xmlfile==2.0.0", "python-docx==1.2.0", "reportlab==5.1.0"]

shutil.rmtree(DIST, ignore_errors=True)
shutil.copytree(ROOT / "web", DIST)

(DIST / "py").mkdir()
with zipfile.ZipFile(DIST / "py" / "utils.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted((ROOT / "utils").glob("*.py")):
        z.write(f, f"utils/{f.name}")

subprocess.run([sys.executable, "-m", "pip", "download", "--quiet", "--no-deps", "--only-binary=:all:",
                "--python-version", "3.14", "-d", str(DIST / "wheels"), *WHEELS], check=True)
wheels = sorted(p.name for p in (DIST / "wheels").glob("*.whl"))
assert len(wheels) == len(WHEELS) and all(w.endswith("-none-any.whl") for w in wheels), wheels
(DIST / "wheels" / "index.json").write_text(json.dumps(wheels))
print(f"Built {DIST} with {len(wheels)} wheels")
