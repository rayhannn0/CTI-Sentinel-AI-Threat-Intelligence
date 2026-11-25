"""Build Lab 10 DOCX with source code and ACTUAL output JSON snapshots if available."""
from pathlib import Path
import json,textwrap
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches,Pt
R=Path(__file__).resolve().parent
FILES=[('Lab 10.1 — Bank Transfer','01_Lab_10_1/lab_10_1.py','lab_10_1.json'),('Activity 10.1 — Exponential Backoff','02_Activity_10_1_Try_It_Yourself/activity_10_1.py','activity_10_1.json'),('Lab 10.2 — Inventory Reservation','03_Lab_10_2/lab_10_2.py','lab_10_2.json'),('Activity 10.2 — Throughput Comparison','04_Activity_10_2_Try_It_Yourself/activity_10_2.py','activity_10_2.json')]
try:
    FONT=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',15)
except OSError:
    try:FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',15)
    except OSError:FONT=ImageFont.load_default()

def screenshot(lines,path,actual):
    wrapped=[]
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=105,replace_whitespace=False,drop_whitespace=False) or [''])
    lines=wrapped[:36]
    w,h=1250,max(190,85+24*len(lines))
    img=Image.new('RGB',(w,h),'#161d2a');draw=ImageDraw.Draw(img)
    draw.rectangle((0,0,w,50), fill='#303c53')
    draw.text((24,15), 'OUTPUT FROM SAVED LOCAL JSON' if actual else 'NOT EXECUTED — NO ACTUAL SCREENSHOT AVAILABLE', font=FONT,fill='#ffffff')
    for i,l in enumerate(lines):draw.text((22,65+i*24),l,font=FONT,fill='#e2edfa')
    img.save(path)

def main():
    doc=Document();norm=doc.styles['Normal'];norm.font.name='Calibri';norm.font.size=Pt(9)
    doc.add_heading('MongoDB Lab 10 — ACID Transactions and Concurrency',0)
    doc.add_paragraph('Lab 10.1 | Activity 10.1 | Lab 10.2 | Activity 10.2',style='Subtitle')
    doc.add_paragraph('Database: lab10 | Replica set: rs10 | MongoDB 7.0 | Dockerized PyMongo runner')
    doc.add_paragraph('Evidence note: Screenshots below are rendered from saved execution-result JSON files. They are not screenshots of the terminal. Missing results are explicitly labeled NOT EXECUTED. Run the labs to populate output/.')
    for title,script,jsonfile in FILES:
        doc.add_page_break();doc.add_heading(title,1)
        doc.add_paragraph('Source file: '+script)
        doc.add_heading('Python script',2)
        for code in (R/script).read_text().splitlines():
            p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0)
            r=p.add_run(code or ' ');r.font.name='Courier New';r.font.size=Pt(6.5)
        doc.add_heading('Execution evidence',2)
        fp=R/'output'/jsonfile
        if fp.exists():
            content=json.dumps(json.loads(fp.read_text()),indent=2).splitlines();actual=True
        else:
            content=['NOT EXECUTED ON THIS MACHINE.','Run: python3 bootstrap.py','Then: docker compose --profile runner run --rm labrunner','Re-run python3 generate_report.py after execution.'];actual=False
        img=R/'output'/('evidence_'+jsonfile.replace('.json','.png'))
        screenshot(content,img,actual)
        doc.add_picture(str(img),width=Inches(6.25))
        doc.add_paragraph('Source: '+('Real saved JSON output from local execution' if actual else 'Placeholder, NOT actual execution'),style='Caption')
    doc.add_page_break();doc.add_heading('Results and integrity criteria',1)
    for note in [
        'Lab 10.1: Successful 250-unit transfer changes A100 1000→750 and B200 500→750. An insufficient transfer must leave both balances and history unchanged.',
        'Activity 10.1: Two explicitly simulated transient errors demonstrate 0.1s/0.2s exponential backoff, then the genuine MongoDB transfer commits once.',
        'Lab 10.2: Eight concurrent attempts for five stock units should yield exactly five orders and zero remaining stock; transient conflicts may be retried.',
        'Activity 10.2: Measured throughput across 1, 4, 8, and 16 workers is environment-dependent. The simulated nontransactional failure demonstrates why atomic order+inventory changes matter.',
        'Demo: Run python3 bootstrap.py, then docker compose --profile runner build labrunner, then docker compose --profile runner run --rm labrunner.',
        'MongoDB Compass: mongodb://127.0.0.1:27417/?directConnection=true. This host URI is intended for inspection, not the multi-node Python runner.',
    ]:doc.add_paragraph(note,style='List Bullet')
    out=R/'Lab10_Report.docx';doc.save(out);print('Generated:',out)
if __name__=='__main__':main()
