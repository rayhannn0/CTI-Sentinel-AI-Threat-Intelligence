"""Generate submission DOCX with full scripts and output images.

When real output logs exist, images are generated from actually recorded stdout.
Before running, sample placeholders are visibly labeled ILLUSTRATIVE, not evidence.
"""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image, ImageDraw, ImageFont
import textwrap
ROOT=Path(__file__).resolve().parent
TASKS=[
 ('Lab 8.1 - Deploy a Local Replica Set','01_Lab_8_1/lab_8_1.py','lab_8_1'),
 ('Lab 8.1 - Try It Yourself - Arbiter','02_Activity_8_1_Try_It_Yourself/activity_8_1.py','activity_8_1'),
 ('Lab 8.2 - Failover and Election','03_Lab_8_2/lab_8_2.py','lab_8_2'),
 ('Lab 8.2 - Try It Yourself - Election Priority','04_Activity_8_2_Try_It_Yourself/activity_8_2.py','activity_8_2'),
]
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
if not Path(FONT).exists(): FONT='/System/Library/Fonts/Menlo.ttc'

def terminal_png(text, filename, real):
    text=(text or '').strip()
    if not text: text='No output found.'
    title='RECORDED TERMINAL OUTPUT' if real else 'ILLUSTRATIVE OUTPUT - NOT AN ACTUAL RUN'
    lines=[]
    for raw in text.splitlines()[:35]:
        lines.extend(textwrap.wrap(raw, width=92, replace_whitespace=False, drop_whitespace=False) or [''])
    lines=lines[:42]
    f=ImageFont.truetype(FONT, 18)
    fb=ImageFont.truetype(FONT, 19)
    w=1500;h=max(180,95+len(lines)*27)
    img=Image.new('RGB',(w,h),'#111827');d=ImageDraw.Draw(img)
    d.rounded_rectangle((15,15,w-15,h-15),radius=18,fill='#1d2939')
    d.text((45,34),title,font=fb,fill=('#6ee7b7' if real else '#fbbf24'))
    y=75
    for line in lines:
        d.text((45,y),line,font=f,fill='#e5e7eb');y+=27
    filename.parent.mkdir(parents=True,exist_ok=True)
    img.save(filename)

def main():
    doc=Document()
    sec=doc.sections[0];sec.top_margin=Inches(.72);sec.bottom_margin=Inches(.72)
    sec.left_margin=Inches(.78);sec.right_margin=Inches(.78)
    norm=doc.styles['Normal'];norm.font.name='Aptos';norm.font.size=Pt(9)
    norm.paragraph_format.space_after=Pt(5)
    doc.add_heading('MongoDB Chapter 8 | Replica Sets & Elections',0)
    doc.add_paragraph('Lab 8.1 + Lab 8.2 • Complete Python scripts, MongoDB specifications and terminal outputs')
    doc.add_paragraph('Database: lab8  |  Replica set: rs0  |  Docker nodes: mongo1, mongo2, mongo3; optional arbiter')
    doc.add_heading('Submission integrity',1)
    doc.add_paragraph('An image labeled RECORDED TERMINAL OUTPUT is generated from the actual stdout saved by run_all.py. An image labeled ILLUSTRATIVE OUTPUT is a placeholder and MUST be replaced with real execution evidence before submission.')
    doc.add_paragraph('Running order: python3 run_all.py → python3 generate_report.py. Run monitoring script in a second Terminal for a live election trace.')
    doc.add_heading('Docker Desktop setup and troubleshooting',1)
    doc.add_paragraph('First launch Docker Desktop, then run python3 check_docker.py. If activity_8_1.py fails with FileNotFoundError: docker, Docker CLI is missing from the Mac PATH or Docker Desktop is not installed. The corrected project detects standard Mac Docker CLI locations and gives an actionable error; Docker Engine must be running.')
    doc.add_heading('Configuration and design',1)
    doc.add_paragraph('Three data-bearing MongoDB containers use Docker-internal addresses mongo1:27017, mongo2:27017, mongo3:27017. Host-side connections use directConnection=true via localhost ports 27217-27219. The arbiter is added last; run_all restores the baseline before priority tests; a data-bearing secondary is made nonvoting first, retaining three election votes. The arbiter stores no application data.')
    for title, rel, tag in TASKS:
        doc.add_page_break()
        doc.add_heading(title,1)
        doc.add_paragraph('Python script: '+rel)
        code=(ROOT/rel).read_text(encoding='utf8')
        for line in code.rstrip().splitlines():
            p=doc.add_paragraph(style='Normal');p.paragraph_format.space_after=Pt(0)
            p.paragraph_format.line_spacing=1.0
            r=p.add_run(line if line else ' ');r.font.name='Consolas';r.font.size=Pt(7)
        doc.add_heading('Terminal output',2)
        log=ROOT/'output'/f'{tag}.txt'
        real=log.exists() and bool(log.read_text(encoding='utf8').strip())
        if real: out=log.read_text(encoding='utf8')
        else:
            out={
             'lab_8_1':'Inserted/upserted on primary: mongo1\nREPLICATION PASS mongo2: {...}\nREPLICATION PASS mongo3: {...}\nrs.status() summary:\nmongo1: PRIMARY healthy=1\nmongo2: SECONDARY healthy=1\nmongo3: SECONDARY healthy=1',
             'activity_8_1':'Arbiter added as third voting member.\nMembers: 4 Election votes: 3\nmongo1: PRIMARY healthy=1\nmongo2: SECONDARY healthy=1\nmongo3: SECONDARY healthy=1\narbiter: ARBITER healthy=1',
             'lab_8_2':'Primary BEFORE stepDown: mongo1\nExpected possible client disconnect during stepDown\nPrimary AFTER stepDown: mongo2\nrs.status() summary',
             'activity_8_2':'Prediction: mongo2\nActual primary: mongo2 | Prediction correct: True\nBaseline priorities restored'
            }[tag]
        shot=ROOT/('output' if real else 'docs')/f'{tag}_terminal.png'
        terminal_png(out,shot,real)
        doc.add_picture(str(shot),width=Inches(6.7))
        if not real: doc.add_paragraph('Placeholder: no actual run recorded. Execute run_all.py and regenerate this document.')
    doc.add_page_break()
    doc.add_heading('Notes & analysis',1)
    doc.add_heading('Why an arbiter?',2)
    doc.add_paragraph('An arbiter participates in elections but does not store the dataset. It can provide a third vote when there are only two voting data-bearing members. It cannot become primary or serve reads, and three full data-bearing members are preferable for production availability.')
    doc.add_heading('Failover and priority expectations',2)
    doc.add_paragraph('On replSetStepDown the old primary yields leadership. An eligible, healthy, sufficiently up-to-date secondary can be elected. A higher priority increases preference but cannot guarantee the outcome. Temporary read failures are expected during election, and the client reconnects to the newly observed primary.')
    doc.add_paragraph('Sources: https://www.mongodb.com/docs/manual/core/replica-set-members/ ; https://www.mongodb.com/docs/manual/core/replica-set-arbiter/ ; https://www.mongodb.com/docs/manual/core/replica-set-elections/')
    out=ROOT/'Lab8_Report.docx';doc.save(out)
    print('Created',out,'with',sum((ROOT/'output'/f'{t}.txt').exists() for _,_,t in TASKS),'recorded activity output(s)')
if __name__=='__main__':main()
