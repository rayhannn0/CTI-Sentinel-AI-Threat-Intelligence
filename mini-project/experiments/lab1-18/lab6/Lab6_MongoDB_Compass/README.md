# MongoDB Chapter 6 – indexing labs

Database in MongoDB Compass: **lab6**. MongoDB URI: `mongodb://localhost:27017/` (override with `MONGODB_URI`).

## Setup on Mac
1. Start MongoDB Server (`mongod`), and ensure MongoDB Compass connects to `mongodb://localhost:27017/`.
2. Extract this ZIP. In Terminal `cd` into `Lab6_MongoDB_Compass`.
3. Install dependencies: `python3 -m pip install -r requirements.txt`.
4. Test connection: `python3 connection.py`.
5. Run all: `python3 run_all.py`. Running Lab 6.1 and 6.2 creates ~121,000 demo products overall, so allow enough local disk space and time.
6. In Compass refresh databases, then expand **lab6**.

Collections: `lab_6_1_products` (50k), `activity_6_1_index_usage` (50k), `lab_6_2_products` (20k), `activity_6_2_covered` (1k).

Each activity has its own `.py`, representative MongoDB import `.json` sample, illustrative output `.png`, and `sample_output.txt`. Python generates the full required dataset at runtime, rather than shipping 50,000 rows as a static JSON attachment. Scripts do not need the JSON imported; JSON is provided for assignment submission/Compass demonstration. For the full generated dataset, use MongoDB Compass Export Collection after running.

Lab 6.1: five indexable query shapes; name search uses anchored case-sensitive `$regex`, which can use a standard B-tree name index. True `$text` search needs a separate text index and cannot be explained before index creation. All explanations are real and printed on your machine.

Lab 6.2: insert timings are live measurements, not predefined promises. The first batch has 10k docs, second after five indexes has 10k; workload comparison is on 10k then 20k then 20k docs respectively. Beware caching and run order when drawing conclusions.

Activity 6.2: projection excludes `_id` to allow an index-only covered query. Verify `totalDocsExamined=0` and no `FETCH` stage.

**DOCX NOTE:** Screenshots labeled `ILLUSTRATIVE / NOT LIVE MONGODB OUTPUT` are previews only. Replace with genuine Terminal screenshots after running to fulfill a strict screenshot-evidence requirement.

No `$jsonSchema` validators or `exclusiveMinimum` are used in Chapter 6, avoiding the Lab 4 validation error.
