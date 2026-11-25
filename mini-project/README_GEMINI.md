# CTI Sentinel Final Assessment — Gemini API update

This ZIP changes only the Appendix A AI Advisor add-on to use **Google Gemini API** instead of Ollama. It does not replace `server.py`, the Lab 1–18 pages or MongoDB data. The same `/advisor` and `/api/advisor/chat` routes are retained.

## Installation / use on Mac

1. In CTI Sentinel's Terminal press Control+C to stop the web server. Keep Docker MongoDB running.
2. Extract this ZIP in `~/Downloads` using `unzip -o CTI_Sentinel_AI_Advisor_Gemini_Update.zip`.
3. `cd ~/Downloads/NoSQL_Sentinel_18_Labs`
4. If the add-on was not installed previously, run `python3 install_advisor.py` once. This step is safe to repeat.
5. Run `bash start_with_gemini.command`. It prompts for your key without displaying or storing it. Paste the key **there**, not into source code or public GitHub.
6. Open `http://127.0.0.1:8765/advisor`; click Seed Threat Knowledge and ask a question.
7. Check `http://127.0.0.1:8765/api/advisor/health` for `gemini_configured:true`. This only confirms a key was supplied, not that authentication succeeded. A successful chat response shows `mode:"llm-rag"` and `model_status:"Gemini ..."`. A refused or quota-limited key shows retrieval-only mode with an error in model status.

**Important:** Since a key was pasted into chat, revoke/rotate it in Google AI Studio and use a **fresh** key for local setup and GitHub submission. Do not commit the key. No Ollama installation is needed. The existing retrieval fallback uses lexical vectors in MongoDB unless a separate embedding model is configured. This is not native Atlas `$vectorSearch`.

## Docker option

Set `GEMINI_API_KEY` in the shell securely before starting `docker compose -f compose.advisor.yaml up --build -d`. The standalone Docker stack is optional and runs separately at http://127.0.0.1:8877/advisor. Do not hard-code the key in Compose or committed files. The main website can run directly using `start_with_gemini.command`.
