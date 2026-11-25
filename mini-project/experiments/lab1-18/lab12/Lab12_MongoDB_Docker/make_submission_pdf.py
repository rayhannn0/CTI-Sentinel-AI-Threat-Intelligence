from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parent
url=(R/'docker_hub_url.txt').read_text().strip()
if not url.startswith('https://hub.docker.com/r/') or 'YOUR' in url or 'PASTE' in url:
 raise SystemExit('First set real published Docker Hub URL in docker_hub_url.txt')
out=R/'Lab12_DockerHub_Submission.pdf'
c=canvas.Canvas(str(out),pagesize=A4);w,h=A4
c.setFont('Helvetica-Bold',19);c.drawString(55,h-75,'Lab 12 - MongoDB Security Submission')
c.setFont('Helvetica',11);c.drawString(55,h-110,'Authentication, RBAC, Field-Level Views, and TLS')
c.drawString(55,h-150,'Published Docker Hub repository:')
c.setFillColorRGB(0.04,0.31,0.68);c.drawString(55,h-173,url);c.linkURL(url,(55,h-180,w-55,h-160),relative=0)
c.setFillColorRGB(0,0,0);c.setFont('Helvetica',10)
c.drawString(55,h-224,'Demonstration requires docker-compose.yml and local bootstrap.py.')
c.drawString(55,h-242,'Certificates and randomized credentials are generated locally and are not bundled.')
c.drawString(55,h-260,'Run: python3 bootstrap.py; docker compose --profile runner run --rm labrunner')
c.save();print('Generated:',out)
