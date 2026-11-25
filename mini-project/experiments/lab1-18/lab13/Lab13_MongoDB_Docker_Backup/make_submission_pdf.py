from pathlib import Path
from urllib.parse import urlparse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
R=Path(__file__).resolve().parent
f=R/'docker_hub_url.txt'
url=f.read_text().strip() if f.exists() else ''
parsed=urlparse(url)
if parsed.scheme!='https' or parsed.netloc!='hub.docker.com' or parsed.path!='/r/rayhann094/lab13-mongodb-assessment':
 raise SystemExit('First save the exact published plain-text Docker Hub URL to docker_hub_url.txt; do not use Markdown syntax.')
out=R/'Lab13_DockerHub_Submission.pdf'
c=Canvas(str(out),pagesize=A4)
w,h=A4
c.setFillColor(HexColor('#183153'));c.rect(0,h-105,w,105,fill=1,stroke=0)
c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',20);c.drawString(48,h-58,'MongoDB Lab 13 — Submission')
c.setFillColorRGB(.15,.19,.25);c.setFont('Helvetica',12);c.drawString(48,h-145,'Docker Hub assessment image')
c.setFillColorRGB(0,.31,.62);c.setFont('Helvetica',11);c.drawString(48,h-175,url)
c.linkURL(url,(48,h-187,w-40,h-158),relative=0)
c.setFillColorRGB(.15,.19,.25);c.setFont('Helvetica',10)
for i,t in enumerate(['Activities: 13.1 Replica Set, 13.1 Monitoring, 13.2 Kubernetes manifests and comparison','Demo: pull the image and use the attached Docker Compose project and README.','Security: locally generated passwords/keyfile are not included in the published image.','Kubernetes requires separate Kubernetes cluster; Docker image does not create K8s pods.']):
 c.drawString(48,h-225-i*22,t)
c.setFont('Helvetica',9);c.drawString(48,45,'Generated from locally configured project; verify Docker Hub link before university submission.')
c.save();print('Generated:',out)
