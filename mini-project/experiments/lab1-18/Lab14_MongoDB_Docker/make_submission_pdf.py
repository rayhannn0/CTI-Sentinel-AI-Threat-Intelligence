import argparse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
p=argparse.ArgumentParser(); p.add_argument("--docker-url",required=True); p.add_argument("--output",default="Lab14_DockerHub_Submission.pdf"); a=p.parse_args()
doc=SimpleDocTemplate(a.output,pagesize=A4,rightMargin=22*mm,leftMargin=22*mm); s=getSampleStyleSheet()
story=[Paragraph("Lab 14 - MongoDB Monitoring and Backup Verification",s["Title"]),Spacer(1,12),Paragraph("Docker Hub Repository",s["Heading2"]),Paragraph(a.docker_url,s["BodyText"]),Spacer(1,12),Paragraph("Lab 14.1: serverStatus metrics, connection counts, operation counters, WiredTiger cache statistics, replica-set lag checks, 30-second logging, threshold alerts, and optional webhook notifications.",s["BodyText"]),Spacer(1,8),Paragraph("Lab 14.2: timestamped backups, restore verification using document counts and content checksums, 1,000/10,000/100,000-document benchmarks, hourly scheduling, and seven-day retention.",s["BodyText"]),Spacer(1,12),Paragraph("Demonstration: Docker Compose runs MongoDB on local port 27817. The lab14 database can be copied to the main localhost:27017 connection with migrate_to_localhost.sh.",s["BodyText"])]
doc.build(story); print("Generated:",a.output)
