# MongoDB Chapter 2 Activities

## Requirements
- Python 3
- Docker Desktop with a MongoDB container running on port 27017
- MongoDB Atlas cluster and database user
- MongoDB Compass
- Python package: `pymongo`

Install:
```bash
python3 -m pip install pymongo
```

Start local MongoDB in Docker (if you do not already have a container):
```bash
docker run -d --name mongodb-ch2 -p 27017:27017 mongo:7
```

Set the Atlas connection string in the VS Code terminal (replace the value with your own URI):
```bash
export ATLAS_URI='mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority'
```
Never commit or submit your real password/connection URI.

For Activity 2.1, both Atlas and Docker are queried. Run from the relevant activity folder:
```bash
python3 activity_2_1.py
python3 try_it_yourself.py
```
The scripts save actual server details to output JSON files after successful execution.

For Activity 2.2, local Docker MongoDB is the default. Run:
```bash
python3 activity_2_2.py
python3 try_it_yourself.py
```
To use Atlas for an Activity 2.2 script, set `MONGODB_URI` before running:
```bash
export MONGODB_URI="$ATLAS_URI"
```

## Compass verification
Connect Compass to `mongodb://localhost:27017`.
- Activity 2.2: open database `chapter2_library`, collection `books`.
- Activity 2.2 Try It Yourself: open database `chapter2_library_try`, collection `books`.
Check `published_year` and `price`. Activity 2.2 updates only years before 2010 by 10%. The additional exercise updates years 2010–2015 inclusive by 5%.

## Screenshot requirement
Run each of the four scripts on your own machine. Capture the terminal showing the command and successful output. For Activity 2.2, also capture Compass showing the relevant collection and updated prices. Insert those genuine screenshots into the clearly marked screenshot areas in `MongoDB_Chapter_2_Report.docx`. The report currently contains placeholders, not fabricated execution screenshots.
