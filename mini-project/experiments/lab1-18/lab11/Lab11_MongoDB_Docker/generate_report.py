from pathlib import Path
import json
from docx import Document
from docx.shared import Pt
R=Path(__file__).resolve().parent
activities=[('Lab 11.1 — Shard Key Decision Matrix','01_Lab_11_1/lab_11_1.py','lab_11_1.json'),('Activity 11.1 — Resharding Research','02_Activity_11_1_Try_It_Yourself/activity_11_1.py','activity_11_1.json'),('Lab 11.2 — Hotspot Benchmark','03_Lab_11_2/lab_11_2.py','lab_11_2.json'),('Activity 11.2 — Analysis','04_Activity_11_2_Try_It_Yourself/activity_11_2.py','activity_11_2.json')]
d=Document();d.add_heading('MongoDB Lab 11 — Shard Key Strategies & Hotspots',0)
d.add_paragraph('Docker demonstration: two shards, one config server, one mongos router. Results must be generated on your own machine.')
for title,script,out in activities:
 d.add_heading(title,1);d.add_paragraph('Script: '+script)
 d.add_heading('Python code',2)
 for line in (R/script).read_text().splitlines():
  para=d.add_paragraph(style='Normal');para.paragraph_format.space_after=Pt(0)
  run=para.add_run(line or ' ');run.font.name='Courier New';run.font.size=Pt(7)
 d.add_heading('Actual execution output',2)
 f=R/'output'/out
 if f.exists():
  raw=json.loads(f.read_text());txt=json.dumps(raw,indent=2,default=str)
 else:txt='NOT EXECUTED — no real output JSON available. Run Docker runner first.'
 for line in txt.splitlines():
  para=d.add_paragraph(style='Normal');para.paragraph_format.space_after=Pt(0)
  run=para.add_run(line or ' ');run.font.name='Courier New';run.font.size=Pt(7)
 d.add_page_break()
d.add_heading('Submission',1);d.add_paragraph('Build and push lab11-mongodb-assessment:latest to your own Docker Hub account. Submit the generated PDF with the real repository URL. A demo needs docker-compose.yml and running cluster services in addition to the runner image.')
d.save(R/'Lab11_Report.docx');print('Generated Lab11_Report.docx')
