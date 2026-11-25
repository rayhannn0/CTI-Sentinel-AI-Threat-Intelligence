# Lab 5 — MongoDB Aggregation Submission

**Database in MongoDB Compass:** `lab5`

## Contents
- `connection.py`: one shared PyMongo connection, localhost:27017 (or `MONGO_URI`)
- `run_all.py`: runs all 4 exercises, in order
- Four independent activity folders, each with a `.py` script, its own `.json` data file, `sample_output.txt`, and `illustrative_output.png`
- `Lab5_Report.docx`: all four complete scripts with illustrative expected-output images
- `verify_project.py`: static Python/JSON checks; does not need MongoDB

## MacBook instructions
1. Start the MongoDB database server, not just MongoDB Compass.
2. Extract the ZIP, then open Terminal **inside `Lab5_MongoDB_Compass`**.
3. `python3 -m pip install -r requirements.txt`
4. `python3 verify_project.py`
5. `python3 connection.py`
6. `python3 run_all.py`
7. Connect MongoDB Compass to `mongodb://localhost:27017/` and refresh; expand **lab5**.

## Collections
- `lab_5_1_orders`
- `activity_5_1_buckets`
- `lab_5_2_products` and `lab_5_2_orders`
- `activity_5_2_products` and `activity_5_2_orders`

Run individual files with `python3 01_Lab_5_1/lab_5_1.py` and analogous paths. Scripts work from VS Code's Code Runner because they use absolute paths derived from `__file__`.

**Data safety:** Each exercise drops and recreates only its own demonstration collections. Do not use the same collection names for valuable data.

**Monthly revenue:** Includes all status categories because the assignment does not request status exclusions. To include only paid/fulfilled orders, add a `$match` stage before `$group`.

**Buckets:** Prices are integer USD in the sample data; `$bucket` boundaries `[0, 50, 201, 1000000000]` place $200 in Medium and $201+ in Large. For fractional-dollar values, use a decimal-currency strategy and boundaries appropriate to your monetary precision.

**Output images:** These are clearly marked illustrative expected results computed from bundled JSON, **not screenshots of a real MongoDB run**. Replace these with actual screenshots after running locally before submitting where execution evidence is required.

## Source reference
https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-05
