from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
ROOT=Path(__file__).resolve().parent
url=(ROOT/'docker_hub_url.txt').read_text().splitlines()[0].strip()
if 'USERNAME' in url or not url.startswith('https://hub.docker.com/r/'):
 raise SystemExit('First edit docker_hub_url.txt with your REAL published Docker Hub URL. No placeholder PDF will be submitted.')
p=ROOT/'Lab9_DockerHub_Submission.pdf'
c=canvas.Canvas(str(p),pagesize=A4);w,h=A4
c.setTitle('Lab 09 MongoDB - Docker Hub Submission')
c.setFont('Helvetica-Bold',18);c.drawString(55,h-70,'Lab 09 — Docker Hub Submission')
c.setFont('Helvetica',11)
c.drawString(55,h-115,'Docker Hub image repository:')
c.setFillColor(colors.blue);c.drawString(55,h-140,url)
c.linkURL(url,(55,h-145,w-55,h-125),relative=0)
c.setFillColor(colors.black)
for i,line in enumerate(['Image contains the Lab 9 Python assessment runner.',
 'A three-node MongoDB replica set is defined in the included docker-compose.yml.',
 'Lab 9.1: Write concern benchmarks (w=1, majority, w=3).',
 'Activity 9.1: Journaling comparisons (j=true vs j=false).',
 'Lab 9.2: Network partition observation.',
 'Activity 9.2: Recovery monitoring and analysis.',
 'Required demo: start Compose stack and execute the tests on a running Docker engine.']):
 c.drawString(55,h-185-22*i,line)
c.save();print('Generated:',p)
