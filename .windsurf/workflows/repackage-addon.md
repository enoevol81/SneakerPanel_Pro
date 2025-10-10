---
description: Run this workflow whenever the source code changes to clean, optimize, and repackage Sneaker Panel Pro for Blender distribution.
auto_execution_mode: 3
---

Repackage Sneaker Panel Pro as a clean distributable add-on build.

1️⃣ Preparation:
- Detect the current BUILD flag from __init__.py (values: "dev", "release", or "market").
- Remove all compiled caches, logs, and temporary files:
  - Delete every __pycache__, .log, .tmp, and any .blend1 or .blend@ files.
  - Remove any existing /dist/ directory.

2️⃣ Code cleanup:
- Run `ruff check . --fix` and `ruff format .`
- Verify there are no lint errors or missing imports.
- Ensure that __init__.py, prefs.py, license_manager.py, and utils/__init__.py all compile successfully.

3️⃣ Exclusions:
Omit the following folders and files from the final package:
- /.git/
- /.github/
- /.vscode/
- /.windsurf/
- /__pycache__/
- /dist/
- generate_keys.py
- issued_keys.csv
- Any README_working.md or internal notes.

4️⃣ Packaging:
- Create a new folder named `SneakerPanelPro/` inside /dist/.
- Copy only these:
  - `__init__.py`, `prefs.py`, `state.py`, `properties.py`
  - `operators/`, `ui/`, `utils/`, `assets/`
  - `LICENSE.txt`, `README.md`
- Zip that folder as `/dist/SneakerPanelPro_<BUILD>.zip`, e.g. `SneakerPanelPro_release.zip`.

5️⃣ Validation:
- Confirm that the ZIP’s top-level structure is `/SneakerPanelPro/__init__.py`.
- Print a summary report with file count and total size in MB.
- Confirm the build name and version from `bl_info`.

6️⃣ Success message:
If all steps pass, print:
"✅ Sneaker Panel Pro <BUILD> build packaged successfully — ready for upload."

