---
description: Run this workflow whenever the source code changes to clean, optimize, and repackage Sneaker Panel Pro for Blender distribution.
auto_execution_mode: 3
---

# 🧠 Sneaker Panel Pro — Repackage Add-on


### 🧩 **Codex Instructions**
1. Delete all `__pycache__` folders and temporary build/log files recursively.
2. Remove any existing `/dist/` directory, then create a new clean `/dist/` folder.
3. Lint and auto-fix Python files with Ruff:
   - Run `ruff check . --fix`
   - Run `ruff format .`
4. Format all `.py` files to PEP-8 using Codex’s built-in formatter if Ruff is unavailable.
5. Create a subdirectory `/dist/SneakerPanelPro` and copy these into it:
   - `__init__.py`, `prefs.py`, `properties.py`, `compat.py`, `state.py`, `README.md`, `LICENSE.txt`
   - Folders: `operators`, `ui`, `utils`, `assets`
6. Exclude `.git`, `.github`, `.vscode`, `.windsurf`, and any `__pycache__/` or `/dist/` directories from the package.
7. Compress `/dist/SneakerPanelPro` into `/dist/SneakerPanelPro_v1.0.zip`.
8. Verify that the resulting ZIP contains a top-level `/SneakerPanelPro/__init__.py`.
9. Report success and display total packaged file count.

---

### ✅ **Usage**
Simply tell Codex:
> “Run the repackage-addon workflow.”

Codex will execute this workflow end-to-end automatically.
