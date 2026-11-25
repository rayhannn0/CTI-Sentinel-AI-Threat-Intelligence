CTI SENTINEL - LAB 18 ONLY LIVE DASHBOARD PATCH

Overlay this zip into ~/Downloads with unzip -o; only server.py, static/sentinel.html, static/sentinel.js, static/lab18.css and this README are replaced/added.
Start the existing Lab18 Docker services and CTI Sentinel. Open http://127.0.0.1:8765/sentinel?lab=18
The dashboard queries threat_intel.full_threats from localhost:27021 (env LAB18_THREAT_URI) and reads ~/Downloads/lab18/Lab18_Threat_Intelligence_Docker_Submission/output/benchmark.csv (env LAB18_OUTPUT_DIR). Fallback uses the existing bundled benchmark_snapshot.csv, always marked saved, not measured live.
MongoDB counts and one live count query latency are measured. False-positive labels are synthetic. Graph community membership is NOT implied by this label. Capacity plans are illustrative, not measured.
