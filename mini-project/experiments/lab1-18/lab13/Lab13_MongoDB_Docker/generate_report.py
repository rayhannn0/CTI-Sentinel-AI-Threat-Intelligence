from pathlib import Path
import json
from docx import Document
from docx.shared import Inches,Pt
R=Path(__file__).resolve().parent
files=[('Lab 13.1 — authenticated replica set','01_Lab_13_1/lab_13_1.py','lab_13_1.json'),('Activity 13.1 — Prometheus exporter','02_Activity_13_1_Try_It_Yourself/activity_13_1.py','activity_13_1.json'),('Lab 13.2 — Kubernetes StatefulSet','03_Lab_13_2/lab_13_2.py','lab_13_2.json'),('Activity 13.2 — Platform comparison','04_Activity_13_2_Try_It_Yourself/activity_13_2.py','activity_13_2.json'),('Lab 13.1 — Actual failover','failover_test.py','failover.json')]

def run():
 d=Document();d.add_heading('MongoDB Lab 13 — Replica Set, Monitoring and Kubernetes',0)
 d.add_paragraph('Lab implementation and evidence report. All output sections indicate whether real execution was recorded. Kubernetes recovery must be separately demonstrated with kubectl.')
 d.add_heading('Project setup',1)
 d.add_paragraph('Three MongoDB 7.0 instances using shared keyFile credentials; authentication enabled; volumes persisted. Prometheus exporter in optional monitoring profile. Kubernetes manifests use a shared Secret, headless Service and per-pod PVCs.')
 for name,path,res in files:
  d.add_page_break();d.add_heading(name,1);d.add_paragraph('Source: '+path)
  d.add_heading('Python source',2)
  content=(R/path).read_text()
  for line in content.splitlines():
   par=d.add_paragraph();par.paragraph_format.space_after=Pt(0)
   run=par.add_run(line or ' ');run.font.name='Courier New';run.font.size=Pt(7)
  d.add_heading('Execution output (JSON)',2)
  out=R/'output'/res
  if out.is_file():
   try: val=json.dumps(json.loads(out.read_text()),indent=2,default=str)
   except Exception: val=out.read_text()
   d.add_paragraph('ACTUAL SAVED OUTPUT FROM LOCAL EXECUTION')
  else:
   val='NOT EXECUTED / NO OUTPUT FILE FOUND. Execute the corresponding activity first.'
   d.add_paragraph('NOT VERIFIED')
  for line in val.splitlines()[:100]:
   par=d.add_paragraph();par.paragraph_format.space_after=Pt(0)
   r=par.add_run(line or ' ');r.font.name='Courier New';r.font.size=Pt(7)
 d.add_page_break();d.add_heading('Kubernetes deployment limitation',1)
 d.add_paragraph('The Docker runner validates Kubernetes manifest structure, but does not run kubectl, deploy Kubernetes pods or verify pod healing. Follow k8s/README.md and provide authenticated replica-set status after pod recreation for actual Lab 13.2 execution evidence.')
 d.add_heading('Docker Hub demonstration',1)
 d.add_paragraph('Image: rayhann094/lab13-mongodb-assessment:latest. The image is an assessment runner and requires the separately supplied Docker Compose project and locally generated secrets. Do not publish .env, keyfile or private keys.')
 target=R/'Lab13_Report.docx';d.save(target)
 print('Generated:',target)
if __name__=='__main__':run()
