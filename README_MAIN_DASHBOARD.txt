CTI Sentinel Unified Main Dashboard (Labs 1-18 + Gemini Advisor)

1. Stop local CTI Sentinel server with Ctrl+C.
2. cd ~/Downloads
3. unzip -o CTI_Sentinel_Unified_Main_Dashboard_Update.zip
4. cd ~/Downloads/NoSQL_Sentinel_18_Labs
5. python3 install_main_dashboard.py
6. bash start_with_gemini.command  (or bash start_sentinel.command if Gemini already configured separately)
7. Open http://127.0.0.1:8765/dashboard

Lab deep links remain /sentinel?lab=1 ... /sentinel?lab=18
Integrated AI Advisor remains /advisor
Standalone container demo remains http://127.0.0.1:8877/advisor

No existing server.py, lab JavaScript, database files, or credentials are overwritten by ZIP extraction.
The installer creates one-time .before_main_dashboard.bak backups of the files it edits.
Restart the server to register the new route. Docker standalone uses a different port and is unchanged.

IMPORTANT: After verifying locally, update the GitHub repository with:
git add server.py static/sentinel.html static/advisor.html static/dashboard.html static/dashboard.css static/dashboard.js install_main_dashboard.py README_MAIN_DASHBOARD.txt
git commit -m "Add unified CTI Sentinel main dashboard"
git push
