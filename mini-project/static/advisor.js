const $=id=>document.getElementById(id);
let busy=false;
function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')}
async function api(path,options){const res=await fetch(path,options);let data;try{data=await res.json()}catch{throw Error('The server did not return JSON')};if(!res.ok)throw Error(data.detail||data.message||'HTTP '+res.status);return data}
function request(body){return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}}
function addBubble(role,content,meta){let bubble=document.createElement('div');bubble.className='bubble '+role;bubble.textContent=content;if(meta){let small=document.createElement('div');small.className='meta';small.textContent=meta;bubble.appendChild(small)}$('messages').appendChild(bubble);$('messages').scrollTop=$('messages').scrollHeight}
async function refresh(){try{let d=await api('/api/advisor/health');$('chunkCount').textContent=d.knowledge_chunks;$('engineIndicator').textContent=d.gemini_configured?'GEMINI API':'RETRIEVAL';$('engineDetail').textContent=d.gemini_configured?'Google '+d.gemini_model:'Set GEMINI_API_KEY to enable AI';$('connectionBadge').textContent=d.database?'MONGODB CONNECTED':'MONGODB OFFLINE';$('serviceState').textContent='MongoDB: '+(d.database?'connected':'offline')+'\nGemini: '+(d.gemini_verified?'Connected (Healthy)':(d.gemini_configured?(d.gemini_status||'Not verified'):'Not configured'))+'\nEmbedding: '+d.embedding_mode;$('serviceState').style.whiteSpace='pre-line'}catch(e){$('serviceState').textContent='Backend: '+e.message;$('connectionBadge').textContent='BACKEND UNAVAILABLE'}}
function loadEvidence(rows){$('evidenceState').textContent=rows.length+' passage(s)';$('sources').innerHTML=rows.length?rows.map(r=>`<div class="evidence"><strong>[${esc(r.label)}] ${esc(r.title)}</strong><small>${esc(r.origin)} · similarity ${Number(r.score||0).toFixed(3)}</small><p>${esc(r.text)}</p></div>`).join(''):'No matching documents. Seed or ingest knowledge.'}
function sync(){ $('platformIndicator').textContent=$('platform').value;$('phaseIndicator').textContent=$('phase').value }
async function history(){let session=$('session').value.trim()||'demo';try{const d=await api('/api/advisor/history?session_id='+encodeURIComponent(session));$('messages').innerHTML='';if(!d.messages.length)addBubble('assistant','No saved messages for this session. Ask a question to begin.');for(let m of d.messages)addBubble(m.role==='user'?'user':'assistant',m.content)}catch(e){addBubble('assistant','History unavailable: '+e.message)}}
$('platform').onchange=sync;$('phase').onchange=sync;
$('session').onchange=history;
$('newSession').onclick=()=>{$('session').value='session-'+Math.random().toString(36).slice(2,9);history()};
$('seedBtn').onclick=async()=>{$('seedBtn').disabled=true;$('seedLog').textContent='Embedding and storing 20 documents...';try{let d=await api('/api/advisor/seed',request({}));$('seedLog').textContent='Saved '+d.chunks_upserted+' chunks from '+d.documents+' teaching documents.';refresh()}catch(e){$('seedLog').textContent='Error: '+e.message}finally{$('seedBtn').disabled=false}};
$('ingestForm').onsubmit=async e=>{e.preventDefault();const b={title:$('docTitle').value,text:$('docText').value,platform:$('platform').value,phase:$('phase').value};try{const d=await api('/api/advisor/ingest',request(b));$('seedLog').textContent='Stored '+d.chunks+' vector chunks ('+d.source_id+')';$('docText').value='';refresh()}catch(err){$('seedLog').textContent='Error: '+err.message}};
$('chatForm').onsubmit=async e=>{e.preventDefault();if(busy)return;const message=$('question').value.trim();if(message.length<2)return;busy=true;$('sendBtn').disabled=true;sync();addBubble('user',message);$('question').value='';let waiting=document.createElement('div');waiting.className='bubble assistant';waiting.textContent='Retrieving evidence and consulting the language model…';$('messages').appendChild(waiting);$('messages').scrollTop=$('messages').scrollHeight;
try{let d=await api('/api/advisor/chat',request({message,session_id:$('session').value.trim()||'demo',platform:$('platform').value,phase:$('phase').value}));waiting.remove();addBubble('assistant',d.answer,(d.mode&&d.mode.startsWith('llm-')&&d.mode!=='llm-unavailable'?'LLM · ':d.mode==='llm-unavailable'?'Unavailable · ':'Retrieval only · ')+d.model_status+' · '+d.history_used+' previous messages · no action executed');loadEvidence(d.sources||[])}catch(err){waiting.textContent='Request failed: '+err.message}finally{busy=false;$('sendBtn').disabled=false}};
refresh();sync();

// Local scanner: scanning and sending to Gemini require separate deliberate consent.
let lastScanId=null;
$('scanConsent').onchange=()=>{$('scanBtn').disabled=!$('scanConsent').checked};
$('geminiScanConsent').onchange=()=>{$('analyzeScanBtn').disabled=!(lastScanId&&$('geminiScanConsent').checked)};
function displayFindings(rows){$('scanFindings').innerHTML=(rows||[]).map(r=>`<div class="scan-entry"><strong>${esc(r.check)}</strong> · <span class="scan-state">${esc(r.status)}</span><div>${esc(r.details)}</div><small>${esc(r.recommendation)}</small></div>`).join('')}
async function scanHistory(){try{const d=await api('/api/advisor/local-scans?session_id='+encodeURIComponent($('session').value.trim()||'demo'));$('scanHistory').innerHTML=d.scans.length?d.scans.map(x=>`<div class="scan-entry">${esc(x.created_at)} · ${x.findings.length} checks · ${x.gemini_analysis?'Gemini assessed':'No AI assessment'}</div>`).join(''):'No scans for this session.'}catch(e){$('scanHistory').textContent='History: '+e.message}}
$('scanBtn').onclick=async()=>{
 if(!$('scanConsent').checked)return;
 $('scanBtn').disabled=true;$('scanStatus').textContent='Running limited read-only checks…';$('scanAnalysis').textContent='';
 lastScanId=null;$('analyzeScanBtn').disabled=true;$('geminiScanConsent').checked=false;
 try{const d=await api('/api/advisor/local-scan',request({session_id:$('session').value.trim()||'demo',confirmation:'RUN_READ_ONLY_MACOS_SCAN'}));lastScanId=d.scan_id;displayFindings(d.findings);$('scanStatus').textContent='Saved '+d.findings.length+' observations in MongoDB · '+d.scope+'. Nothing sent to Gemini.';scanHistory()}
 catch(e){$('scanStatus').textContent='Scan unavailable: '+e.message}
 finally{$('scanBtn').disabled=!$('scanConsent').checked}
};
$('analyzeScanBtn').onclick=async()=>{
 if(!lastScanId||!$('geminiScanConsent').checked)return;
 $('analyzeScanBtn').disabled=true;$('scanAnalysis').textContent='Submitting limited scan summary to Gemini…';
 try{const d=await api('/api/advisor/analyze-local-scan',request({session_id:$('session').value.trim()||'demo',scan_id:lastScanId,confirmation:'SEND_SUMMARY_TO_GEMINI'}));$('scanAnalysis').textContent=d.ok?d.model_status+'\n\n'+d.analysis:d.message+' '+d.model_status;scanHistory()}
 catch(e){$('scanAnalysis').textContent='Analysis error: '+e.message}
 finally{$('analyzeScanBtn').disabled=!(lastScanId&&$('geminiScanConsent').checked)}
};
$('session').addEventListener('change',()=>{lastScanId=null;$('analyzeScanBtn').disabled=true;$('scanConsent').checked=false;$('scanBtn').disabled=true;$('geminiScanConsent').checked=false;scanHistory()});
$('newSession').addEventListener('click',()=>{lastScanId=null;$('analyzeScanBtn').disabled=true;$('scanConsent').checked=false;$('scanBtn').disabled=true;$('geminiScanConsent').checked=false;scanHistory()});
scanHistory();

// Controlled quarantine: never select a file autonomously or use Gemini as approval.
let reviewedFile=null;
function resetQuarantine(){reviewedFile=null;$('quarantineConsent').checked=false;$('applyQuarantine').disabled=true}
$('quarantineName').addEventListener('input',()=>{resetQuarantine();$('quarantinePreview').textContent='Preview required after any filename change.'});
$('quarantineConsent').addEventListener('change',()=>{$('applyQuarantine').disabled=!(reviewedFile&&$('quarantineConsent').checked)});
$('previewQuarantine').onclick=async()=>{
 resetQuarantine();$('quarantinePreview').textContent='Checking selected file fingerprint…';
 try{
  const d=await api('/api/advisor/quarantine/preview',request({session_id:$('session').value.trim()||'demo',filename:$('quarantineName').value.trim()}));
  reviewedFile={filename:d.filename,sha256:d.sha256};
  $('quarantinePreview').textContent='File: '+d.filename+' · '+d.size+' bytes\nSHA-256: '+d.sha256+'\nUnclassified file. Quarantine does NOT prove it is malicious.';
 }catch(e){$('quarantinePreview').textContent='Preview failed: '+e.message}
};
$('applyQuarantine').onclick=async()=>{
 if(!reviewedFile||!$('quarantineConsent').checked)return;
 if(!window.confirm('Move '+reviewedFile.filename+' from Downloads to private quarantine? This may affect applications relying on it. You can restore it later.'))return;
 $('applyQuarantine').disabled=true;$('quarantineStatus').textContent='Moving selected file to private quarantine…';
 try{
  const d=await api('/api/advisor/quarantine/apply',request({session_id:$('session').value.trim()||'demo',filename:reviewedFile.filename,sha256:reviewedFile.sha256,confirmation:'QUARANTINE_THIS_EXACT_FILE'}));
  $('quarantineStatus').textContent=d.message+' ID: '+d.quarantine_id;
  resetQuarantine();quarantineHistory();
 }catch(e){$('quarantineStatus').textContent='No change completed: '+e.message;resetQuarantine()}
};
async function quarantineHistory(){
 try{
  const d=await api('/api/advisor/quarantine/history?session_id='+encodeURIComponent($('session').value.trim()||'demo'));
  const el=$('quarantineHistory');el.innerHTML='';
  if(!d.items.length){el.textContent='No quarantined files in this session.';return}
  for(const item of d.items){
   const div=document.createElement('div');div.className='scan-entry';
   div.textContent=item.filename+' · '+item.state+' · SHA-256 '+item.sha256.slice(0,16)+'…';
   if(item.state==='quarantined'){
    const btn=document.createElement('button');btn.className='btn subtle';btn.type='button';btn.textContent='Restore this file';
    btn.onclick=async()=>{
     if(!window.confirm('Restore '+item.filename+' back to Downloads? Do not open it until you have verified it is safe.'))return;
     btn.disabled=true;
     try{const r=await api('/api/advisor/quarantine/restore',request({session_id:$('session').value.trim()||'demo',quarantine_id:item.quarantine_id,confirmation:'RESTORE_THIS_EXACT_FILE'}));$('quarantineStatus').textContent=r.message;quarantineHistory()}
     catch(e){$('quarantineStatus').textContent='Restore failed: '+e.message;btn.disabled=false}
    };
    div.appendChild(btn)
   }
   el.appendChild(div)
  }
 }catch(e){$('quarantineHistory').textContent='History unavailable: '+e.message}
}
$('session').addEventListener('change',()=>{resetQuarantine();quarantineHistory()});
$('newSession').addEventListener('click',()=>{resetQuarantine();quarantineHistory()});
quarantineHistory();


/* CTI_CHAT_SCAN_V2: direct local scan commands, no cloud transmission. */
(() => {
 const form=document.getElementById('chatForm'), question=document.getElementById('question');
 if(!form || !question) return;
 let running=false;
 const intent=/^(?:(?:please|can you|could you)\s+)?(?:scan\s+(?:my\s+)?(?:mac(?:book|os)?|system|computer|device)(?:\s+for\s+[\w\s-]+)?|(?:run|start|perform)\s+(?:a\s+)?(?:local\s+)?(?:security|system|macos|vulnerability)\s+scan|check\s+my\s+(?:system|mac(?:book)?|computer)\s+for\s+(?:security\s+)?(?:risks|threats|vulnerabilities|security issues))\s*[.!?]*$/i;
 function bubble(role, value){const el=document.createElement('div');el.className='bubble '+role;el.textContent=value;el.style.whiteSpace='pre-wrap';const area=document.getElementById('messages');area.appendChild(el);area.scrollTop=area.scrollHeight;return el;}
 async function json(url,opts){const r=await fetch(url,opts);const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail||d));return d;}
 form.addEventListener('submit',async e=>{
 const message=question.value.trim();if(!intent.test(message))return;
 e.preventDefault();e.stopImmediatePropagation();if(running||document.getElementById('sendBtn')?.disabled)return;
 if(!window.confirm('Run a read-only security check on the Mac hosting CTI Sentinel? Results stay local; no files or settings will be changed.'))return;
 running=true;const send=document.getElementById('sendBtn');if(send)send.disabled=true;question.value='';bubble('user',message);const out=bubble('assistant','Running local macOS security check…');
 try{
 const spec=await json('/openapi.json');let schema=spec.paths['/api/advisor/local-scan']?.post?.requestBody?.content?.['application/json']?.schema;if(!schema)throw Error('Local scanner endpoint not available.');
 if(schema.$ref)schema=spec.components.schemas[schema.$ref.split('/').pop()];
 const props=schema.properties||{}, body={};let consent=false;
 for(const [key,p] of Object.entries(props)){
 if(key==='session_id')body[key]=document.getElementById('session')?.value.trim()||'demo';
 else if(key==='confirmation'&&p.const==='RUN_READ_ONLY_MACOS_SCAN'){body[key]=p.const;consent=true;}
 else if(/^(consent|confirm|confirmed|allow_local_scan|consent_local_scan|scan_consent|user_consent|consent_to_scan|confirm_scan|allow_scan|authorized|acknowledged)$/i.test(key)&&p.type==='boolean'){body[key]=true;consent=true;}
 else if(/gemini|cloud|share|upload|transmit/i.test(key)&&p.type==='boolean')body[key]=false;
 else if(key==='platform')body[key]='macOS';
 }
 if(!consent)throw Error('Scanner consent schema not recognized. Use the existing Scan My Mac button.');
 for(const key of schema.required||[])if(!(key in body))throw Error('Unsupported required scanner field: '+key);
 const d=await json('/api/advisor/local-scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(d.ok===false)throw Error(d.message||'Scanner reported failure');
 const findings=d.findings||d.scan?.findings||d.observations||d.scan?.observations;
 if(!Array.isArray(findings)){out.textContent='LOCAL SCANNER RESPONSE (HTTP success)\n'+JSON.stringify(d,null,2)+'\n\nConfiguration observations only; no remediation executed.';return;}
 out.textContent='LOCAL SECURITY CHECK COMPLETED\n'+findings.length+' observations\n\n'+findings.map((f,i)=>`${i+1}. ${typeof f==='string'?f:Object.entries(f).map(([k,v])=>k+': '+(typeof v==='object'?JSON.stringify(v):String(v))).join('\n')}`).join('\n\n')+'\n\nThese are configuration observations, not proof of malware. No remediation executed.';
 }catch(err){out.textContent='Scan unavailable: '+err.message;}finally{running=false;if(send)send.disabled=false;}
 },true);
})();
