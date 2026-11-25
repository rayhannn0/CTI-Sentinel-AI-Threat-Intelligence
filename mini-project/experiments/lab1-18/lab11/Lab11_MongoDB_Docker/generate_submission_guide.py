from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from xml.sax.saxutils import escape
r=Path(__file__).resolve().parent
p=r/'Lab11_Submission_Guide.pdf'
st=getSampleStyleSheet();d=SimpleDocTemplate(str(p),pagesize=A4)
story=[Paragraph('Lab 11 — Execution and Docker Hub Submission Guide',st['Title']),Spacer(1,22)]
for title,items in [('Run the sharded cluster',['Download and extract Lab11_MongoDB_Docker.zip','Open Terminal and cd into the actual extracted Lab11_MongoDB_Docker folder','python3 bootstrap.py','docker compose --profile runner build labrunner','docker compose --profile runner run --rm labrunner']),('Check real results',['Compass URI: mongodb://127.0.0.1:27517/?directConnection=true','Look for lab11.hotspot_data and lab11.even_data; each must contain 10,000 documents','Generate evidence Word report: python3 -m pip install -r requirements.txt ; python3 generate_report.py']),('Publish and submit',['docker login','docker tag lab11-mongodb-assessment:latest rayhann094/lab11-mongodb-assessment:latest','docker push rayhann094/lab11-mongodb-assessment:latest','Put the real plain Docker URL in docker_hub_url.txt','python3 make_submission_pdf.py','Submit Lab11_DockerHub_Submission.pdf to the university portal'])]:
    story.append(Paragraph(title,st['Heading2']))
    for item in items:story.extend([Paragraph(escape(item),st['BodyText']),Spacer(1,9)])
story.extend([Spacer(1,15),Paragraph('Important: This is a setup guide, NOT a claim that Docker Hub already contains the image. A live demonstration needs both the runner image and the accompanying Docker Compose cluster.',st['BodyText'])])
d.build(story)
print('Generated',p)
