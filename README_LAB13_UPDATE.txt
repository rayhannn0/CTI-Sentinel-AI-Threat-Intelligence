CTI Sentinel – Lab 13-only update (reference-style security workbench)

1. Stop the running CTI Sentinel web server with Control+C. Leave Docker running.
2. Download the ZIP to ~/Downloads.
3. From Terminal:
   cd ~/Downloads
   unzip -o CTI_Sentinel_Lab13_Only_Update.zip
   cd ~/Downloads/NoSQL_Sentinel_18_Labs
   bash start_sentinel.command
4. Open http://127.0.0.1:8765/sentinel?lab=13 and hard refresh (Command+Shift+R).

Only server.py, static/sentinel.html, static/sentinel.js and static/lab13.css are required for this patch; no database volumes are touched. Keep current static/lab12.css and static/sentinel.css in place.

Lab 13 now previews security roles using a REAL MongoDB $project view in an isolated database lab13_security_demo. Views omit sensitive fields and reject writes; the role dropdown is only a teaching preview. Real authentication/RBAC accounts, TLS and CSFLE are NOT configured by this patch. The original Lab 13 production-deployment checks are preserved below the new panel.

Your existing Lab 11 live mongos cluster and Lab 12 $jsonSchema validation routes remain unchanged.
