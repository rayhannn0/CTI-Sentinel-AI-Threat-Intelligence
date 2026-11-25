"""Generate instructor submission PDF only after Docker image is publicly published."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from xml.sax.saxutils import escape
R=Path(__file__).resolve().parent

def main():
    url=(R/'docker_hub_url.txt').read_text().strip()
    if not url.startswith('https://hub.docker.com/r/') or any(ch in url for ch in '[]() <>\n'):
        raise SystemExit('First replace docker_hub_url.txt with your REAL published Docker Hub URL as plain text (not a Markdown link).')
    out=R/'Lab10_DockerHub_Submission.pdf'
    styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(str(out),pagesize=A4,title='Lab 10 Docker Hub submission',leftMargin=48,rightMargin=48,topMargin=55,bottomMargin=55)
    story=[Paragraph('MongoDB Lab 10 — Docker Hub Submission',styles['Title']),Spacer(1,28),Paragraph('Completed assessment: Lab 10.1, Activity 10.1, Lab 10.2, Activity 10.2',styles['BodyText']),Spacer(1,18),Paragraph('Published Docker repository:',styles['Heading2']),Paragraph(f'<link href="{escape(url)}" color="blue">{escape(url)}</link>',styles['BodyText']),Spacer(1,24),Paragraph('Demonstration requirements',styles['Heading2'])]
    for line in ['Use the accompanying docker-compose.yml to start MongoDB replica-set services.','Initialize the replica set with python3 bootstrap.py.','Run docker compose --profile runner run --rm labrunner to execute all four activities.','The Docker image contains the assessment scripts; MongoDB servers use official mongo:7.0 images.']:
        story.append(Paragraph('• '+escape(line),styles['BodyText']));story.append(Spacer(1,10))
    doc.build(story)
    print('Generated:',out)
if __name__=='__main__':main()
