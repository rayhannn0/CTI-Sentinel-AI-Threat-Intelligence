# Create report PDF from actual benchmark JSON
from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.units import inch

OUT=Path('output');OUT.mkdir(exist_ok=True)

def build():
    src=OUT/'benchmark.json'
    if not src.exists():raise SystemExit('Run python -m scripts.benchmark before generating measured report')
    data=json.loads(src.read_text());rows=data['results'];styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle',parent=styles['Title'],fontSize=20,leading=24,textColor=colors.HexColor('#14354b'),spaceAfter=14))
    styles.add(ParagraphStyle(name='Small',parent=styles['Normal'],fontSize=9,leading=13,spaceAfter=7))
    path=OUT/'Lab18_Comparative_Report.pdf'
    d=SimpleDocTemplate(str(path),pagesize=(595,842),rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    story=[]
    def h(t):story.append(Paragraph(t,styles['Heading2']));story.append(Spacer(1,7))
    def body(t):story.append(Paragraph(t,styles['Small']))
    story.append(Paragraph('LAB 18 | THREAT INTELLIGENCE',styles['ReportTitle']))
    body('Comparative study of MongoDB, Cassandra, and Neo4j - synthetic false-positive detection capstone')
    body('<b>Status:</b> Measured benchmarks on the local Docker environment. Repository URL: https://hub.docker.com/r/rayhann094/lab18-threat-intelligence (verify push before submitting).')
    h('1. Executive summary')
    body('A polyglot approach is recommended: MongoDB for rich source and threat investigations; Cassandra for query-driven, high-volume chronological/event and materialized daily views; Neo4j for graph relationship exploration and candidate suspicious communities. False-positive flags here are synthetic heuristics, not calibrated security judgments.')
    h('2. Architecture / Methodology')
    body('Synthetic threat emitter -> batch writer -> MongoDB (full_threats + source summaries), Cassandra (threats_by_source, threats_by_type, threats_by_target, daily_volume), Neo4j (Source - REPORTED -> Threat; Source - SUSPICIOUS - Source). The same deterministic source records populate all systems. 10 timed samples per query+backend; median client-side latency. Host hardware and workload contention affect results.')
    body('MongoDB seeded event count before benchmark: '+str(data.get('seeded_mongo_events_before_benchmark','unknown'))+'. All results are local, not claimed production throughput.')
    h('3. Schema design')
    body('<b>MongoDB:</b> full_threats(threat_id,from_source,timestamp,day,threat_type,target,fingerprint,confidence,is_false_positive); threats(from_source,total_count,recent_threats[<=50]). Indexes on (from_source,timestamp), target+timestamp, day+type.')
    body('<b>Cassandra:</b> partition-oriented threats_by_source, threats_by_type, threats_by_target; precomputed daily_volume keyed by day. Denormalized writes provide read speed with additional write amplification and consistency overhead.')
    body('<b>Neo4j:</b> Source and Threat nodes linked by REPORTED; inferred SUSPICIOUS source-source edges weighted by shared fingerprints. Query propagation and connected components are transparent graph heuristics.')
    h('4. Query performance - measured')
    matrix=[['Pattern','MongoDB','Cassandra','Neo4j']]
    for pat in ['threat_history','target_spread','daily_volume','insert_10_events']:
        vals={r['backend']:r['median_ms'] for r in rows if r['pattern']==pat}
        matrix.append([pat]+[f"{vals.get(k,'-')} ms" for k in ('mongodb','cassandra','neo4j')])
    t=Table(matrix,colWidths=[152,113,113,113],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce9ef')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#bacbd3')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fa')]),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9)]))
    story.append(t);story.append(Spacer(1,12))
    body('<b>Interpretation caution:</b> Cassandra daily_volume is preaggregated; the other two execute aggregation at query time. Cassandra throughput inserts into three denormalized tables; this is not an equivalent single-row write comparison. These are pattern-specific end-to-end latency observations, not universal database rankings.')
    h('5. Operational complexity and scaling')
    body('MongoDB: built-in indexing and flexible source documents; replica sets for resilience; sharding when datasets and write demand outgrow one server. Cassandra: token-based partitioning and multi-node replication; requires disciplined partition keys, repair, compaction and multiple materialized access patterns. Neo4j: high-level graph queries; memory footprint depends strongly on relationship density. The Community Docker deployment is standalone, not a production sharded cluster.')
    body('Illustrative capacity planning assumptions only (not benchmarked): avg logical threat record 1 KB before indexes/replication and graph expansion. 1M: ~1 GB raw per logical representation; 10M: ~10 GB; 100M: ~100 GB. Multiple backend copies, denormalized rows, graph relationships, indexes and backups multiply physical footprint substantially. Do not treat these as measured hardware minimums.')
    h('6. Recommendations')
    body('Use MongoDB for history drilldown and incident details, Cassandra for durable volume/time-window lookups at scale, and Neo4j for suspicious-source relationship searches and community candidates. Validate false positives against independent threat indicators and analyst labels before taking action. Add observability, backups and authentication before any production deployment.')
    h('7. Demonstration and reproducibility')
    body('Commands: docker compose up --build -d; docker compose exec app python -m scripts.seed --count 100000; docker compose exec app python -m scripts.benchmark; docker compose exec app python -m scripts.communities; docker compose exec app python -m scripts.report. The first run can take substantial resources. Dataset is synthetic.')
    body('References: MongoDB manual /manual/sharding/ ; Neo4j Operations Manual /scalability/scaling-with-neo4j/ ; Apache Cassandra docs /cassandra/managing/operating/ .')
    d.build(story);print('REPORT GENERATED:',path)
if __name__=='__main__':build()
