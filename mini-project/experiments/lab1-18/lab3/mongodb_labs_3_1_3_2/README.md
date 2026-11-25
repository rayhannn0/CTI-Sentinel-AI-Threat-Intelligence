# MongoDB Labs 3.1 and 3.2

Includes all numbered instructions and both **Try it yourself** activities.

## Files
- `connection.py` — shared MongoDB connection and ping check
- `lab_3_1.py` — embedded course schema, validation, inserts, Monday query, instructor students, prerequisite reference activity
- `lab_3_2.py` — 5 posts/10 comments, `$lookup`, embedded migration, query-count comparison, 10,000-comment activity
- `activity_3_1.py` — separate runnable Try it yourself: course prerequisite references
- `activity_3_2.py` — separate runnable Try it yourself: 10,000 referenced comments and pagination
- `TRY_IT_YOURSELF_ANSWERS.md` — written activity answers and design justifications
- `requirements.txt` — Python dependency

## Run on macOS
1. Start MongoDB locally (or use Docker):
   ```bash
   docker run -d --name mongodb-labs -p 27017:27017 mongo:7
   ```
   If you already have a MongoDB instance listening on port 27017, skip this command.
2. In Terminal, navigate to the extracted folder:
   ```bash
   cd mongodb_labs_3_1_3_2
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   python lab_3_1.py
   python lab_3_2.py
   python activity_3_1.py
   python activity_3_2.py
   ```
3. To use a different MongoDB connection string:
   ```bash
   export MONGO_URI='mongodb://localhost:27017/'
   ```

**Warning:** Running the labs drops and recreates the demo collections `university_lab_db.courses`, `blog_lab_db.posts`, `blog_lab_db.comments`, and `blog_lab_db.embedded_posts`, plus the activity-specific demo collections. Use a development MongoDB instance.

## Design explanations
- **Lab 3.1:** Store prerequisite *course codes* in each course, referencing independently managed courses. This avoids duplicating whole prerequisite course documents. The example prerequisite `CS201` is an illustrative external course code; it is not inserted in this three-course sample.
- **Lab 3.2:** A referenced design uses two queries if fetching a post and its comments separately, or one aggregation query with `$lookup`. Embedding requires one direct read but may become expensive as comments grow. For 10,000 comments, keep a separate comments collection indexed on `post_id` and paginate results. MongoDB BSON documents have a 16 MB size limit.
