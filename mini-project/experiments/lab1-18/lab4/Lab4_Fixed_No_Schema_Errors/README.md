# Lab 4 — Fixed MongoDB Compass Submission

**Database shown in Compass:** `lab4`  
**Shared connection:** `connection.py`  
**Each of the four activity folders contains a Python script, products.json, sample output, and an illustrative output image.**

## Error fixed
The MongoDB error `'$jsonSchema keyword minimum must be present if exclusiveMinimum is present'` was caused by a validator involving `exclusiveMinimum`. **All four scripts now omit `exclusiveMinimum` entirely** and validate positive sample prices using `"minimum": 0.01`. This permits prices from 0.01 upwards (consistent with the two-decimal-place sample product prices). Negative or zero prices are rejected. The shared MongoDB connection stays unchanged.

## Run on your Mac
1. Start the MongoDB **server** (Compass itself is only a viewer).
2. Open Terminal in this extracted folder.
3. `python3 -m pip install -r requirements.txt`
4. `python3 verify_project.py` — checks Python syntax and finds incompatible validator text without requiring MongoDB.
5. `python3 connection.py` — confirms MongoDB connectivity.
6. `python3 run_all.py` — runs all four activities.
7. Open MongoDB Compass, connect to `mongodb://localhost:27017/`, and refresh the sidebar. Expand `lab4`.

The collections created are:
- `lab_4_1_products`
- `activity_4_1_search`
- `lab_4_2_products`
- `activity_4_2_import`

**Run individually** with `python3 01_Lab_4_1/lab_4_1.py` (and similarly for other folders). The scripts find `connection.py` in the root even when launched from VS Code Code Runner.

**Attention:** Each script drops and rebuilds its OWN demonstration collection each run. Use this only for lab data. The DOCX illustrative outputs are not authentic run screenshots; replace them with screenshots of your own MongoDB execution if required by your teacher.

**Note on monetary precision:** For real currency data, store integer paise/cents or Decimal128 instead of binary floating-point. The 0.01 minimum is intended for this lab's two-decimal sample prices.
