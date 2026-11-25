from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parent
url=(R/'docker_hub_url.txt').read_text().strip()
if not url.startswith('https://hub.docker.com/r/') or '[' in url or 'USERNAME' in url or ']' in url:
 raise SystemExit('Edit docker_hub_url.txt with the real Docker Hub URL, then rerun.')
path=R/'Lab11_DockerHub_Submission.pdf'
doc=SimpleDocTemplate(str(path),pagesize=A4)
styles=getSampleStyleSheet()
story=[Paragraph('MongoDB Lab 11 — Docker Hub Submission',styles['Title']),Spacer(1,20),Paragraph('Docker image repository:',styles['Heading2']),Paragraph(f'<link href="{url}">{url}</link>',styles['Normal']),Spacer(1,15),Paragraph('Demonstration: the repository contains the Python assessment runner image. Use the project Docker Compose configuration to start mongos, config server, and two shards before executing the runner.',styles['Normal'])]
doc.build(story);print('Generated:',path)
