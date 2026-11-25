from pathlib import Path
import json
from docx import Document
from docx.shared import Pt
R=Path(__file__).resolve().parent
files=[('Lab 12.1 - Authentication and RBAC','01_Lab_12_1/lab_12_1.py','lab_12_1.json'),('Try It Yourself 12.1 - Redacted View','02_Activity_12_1_Try_It_Yourself/activity_12_1.py','activity_12_1.json'),('Lab 12.2 - TLS Enforcement','03_Lab_12_2/lab_12_2.py','lab_12_2.json'),('Try It Yourself 12.2 - Certificate Chain','04_Activity_12_2_Try_It_Yourself/activity_12_2.py','activity_12_2.json')]
d=Document();d.add_heading('MongoDB Lab 12 - Security',0);d.add_paragraph('Execution evidence is sourced exclusively from actual JSON files after running the Docker assessment.')
for title,script,result in files:
 d.add_page_break();d.add_heading(title,1);d.add_paragraph('Script: '+script)
 d.add_heading('Python source',2)
 for l in (R/script).read_text().splitlines():
  para=d.add_paragraph();para.paragraph_format.space_after=Pt(0);run=para.add_run(l or ' ');run.font.name='Consolas';run.font.size=Pt(7)
 d.add_heading('Recorded output',2)
 f=R/'output'/result
 if f.exists():
  text=json.dumps(json.loads(f.read_text()),indent=2,default=str)
  if len(text)>14000:text=text[:14000]+'\n... output truncated for document; full JSON in output/'
 else:text='NOT EXECUTED: Run Docker assessment before submission. This is not evidence.'
 for l in text.splitlines():
  para=d.add_paragraph();para.paragraph_format.space_after=Pt(0);run=para.add_run(l or ' ');run.font.name='Consolas';run.font.size=Pt(7)
d.add_page_break();d.add_heading('Security implementation notes',1)
for s in ['MongoDB requires TLS for all connections; plaintext is rejected.','Application accounts use custom least-privilege roles for individual collections.','employees_public is a $project view that removes salary; readers cannot query employees directly.','The CA signs both a server certificate and a client certificate, generated at bootstrap.','Password authentication uses SCRAM; the client certificate is only presented to the TLS layer.','Root passwords and private keys are generated on the operator computer and excluded from Docker images and the downloadable ZIP.']:
 d.add_paragraph(s,style='List Bullet')
out=R/'Lab12_Report.docx';d.save(out);print('Generated:',out)
