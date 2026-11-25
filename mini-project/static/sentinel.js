const $=id=>document.getElementById(id);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(Number(n||0));
let labs=[],labActions=[],current=10,bankState=null,working=false;
const forms={
 1:{op:'create',fields:[['name','Document name','CTI report'],['status','Status','active']],label:'Create MongoDB document'},
 2:{op:'create',fields:[['title','Book title','MongoDB Fundamentals'],['year','Publication year','2007'],['price','Price ($)','45']],label:'Add book'},
 3:{op:'create',fields:[['code','Course code','CS401'],['title','Course title','Database Systems'],['instructor','Instructor','Dr Kumar'],['days','Days','Monday,Wednesday'],['room','Room','A-101']],label:'Save course'},
 4:{op:'create',fields:[['sku','SKU','LIVE-01'],['name','Product name','Wireless keyboard'],['price','Price ($)','29'],['stock','Stock quantity','12'],['tags','Comma-separated tags','electronics,wireless']],label:'Save product'},
 5:{op:'create',fields:[['customer','Customer','Alice'],['sku','Product SKU','A'],['quantity','Quantity','2']],label:'Place order'},
 15:{op:'create',fields:[['tenant','Tenant ID','tenant-1'],['title','Task title','Investigate security events']],label:'Create task'},
 17:{op:'create',fields:[['source','Document source','Threat report'],['text','Text passage','Analyze suspicious login activity and investigate false positive indicators.']],label:'Save passage'}
};
async function api(url,opt){let response=await fetch(url,opt);let data=await response.json();if(!response.ok)throw Error(data.detail||data.message||String(response.status));return data}
function request(body){return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}}
function log(message,kind='info'){let at=new Date().toLocaleTimeString();$('terminal').textContent=`[${at}] ${message}`;$('terminal').style.color=kind==='error'?'#ffb2bd':'#aaf3ce'}
function setBusy(v){working=v;['validTransfer','failureTransfer','rollbackTransfer','resetBank','refreshBank'].forEach(id=>$(id).disabled=v)}
function bankRender(state){if(!state)return;bankState=state;$('replicaStatus').textContent=state.transaction_ready?'PRIMARY READY':'STANDALONE';$('replicaStatus').style.color=state.transaction_ready?'#8ef3b2':'#ffb887';$('replicaName').textContent=state.replica_set||'Replica set required for ACID';$('txCount').textContent=state.transactions??0;$('dbStatus').textContent='CONNECTED';$('dbStatus').style.color='#b3ff92';$('connection').textContent='● Live MongoDB connected';let a=state.accounts?.find(x=>x.account_id==='ACC-1001'),b=state.accounts?.find(x=>x.account_id==='ACC-1002');$('balanceA').textContent=a?money(a.balance):'Not seeded';$('balanceB').textContent=b?money(b.balance):'Not seeded';$('versionA').textContent=a?.version??'—';$('versionB').textContent=b?.version??'—';$('historyCount').textContent=`${state.history?.length||0} entries`;let all=state.history||[];$('auditRows').innerHTML=all.length?all.map(x=>`<div class="audit-item"><div class="auditline"><strong>${escapeHTML(x.source)} → ${escapeHTML(x.target)}</strong><span>${money(x.amount)}</span><b class="${x.status==='COMMITTED'?'committed':'failed'}">${escapeHTML(x.status)}</b></div><small>${escapeHTML(x.time?.replace('T',' ').slice(0,19))} · ${escapeHTML(x.message)}</small></div>`).join(''):'<div class="empty">No transfers executed yet. Initialize balances, then try a transfer.</div>';$('diagnostics').innerHTML=`<span>Topology: <strong>${escapeHTML(state.replica_set||'standalone')}</strong></span><span>Transactions: <strong style="color:${state.transaction_ready?'#85f6bb':'#ffb887'}">${state.transaction_ready?'AVAILABLE':'UNAVAILABLE'}</strong></span>`;$('bankWarning').classList.toggle('hidden',!!state.transaction_ready);$('bankWarning').textContent='ACID transactions need your rsLab10 replica set. Restart this website with LAB18_MONGO_URI="mongodb://localhost:27022/?replicaSet=rsLab10". Your Lab 18 data stays on port 27021.';}
async function loadBank(){try{let d=await api('/api/sentinel/bank');if(!d.ok)throw Error(d.message);bankRender(d)}catch(e){$('dbStatus').textContent='OFFLINE';$('connection').textContent='● MongoDB connection failed';log('Database connection failed: '+e.message,'error')}}
async function resetBank(){setBusy(true);try{let d=await api('/api/sentinel/bank/reset',{method:'POST'});if(!d.ok)throw Error(d.message);log('[Session] '+d.message);bankRender(d.state)}catch(e){log(e.message,'error')}finally{setBusy(false)}}
async function runTransfer(options={}){setBusy(true);try{const amount=options.amount??Number($('amount').value);if(!(amount>0)){log('Enter a positive amount.','error');return}let d=await api('/api/sentinel/bank/transfer',request({amount,source:'ACC-1001',target:'ACC-1002',test_failure:!!options.test_failure}));log(`${d.ok?'[COMMIT]':'[ROLLBACK]'} ${d.message} ${d.tx_id||''}`,d.ok?'info':'error');if(d.state)bankRender(d.state)}catch(e){log(e.message,'error')}finally{setBusy(false)}}
async function inventory(op){$('gpuResult').textContent='Running MongoDB action…';try{let d=await api('/api/models/command',request({lab:10,operation:op,data:op==='reserve'?{quantity:Number($('gpuQty').value)}:{}}));$('gpuResult').textContent=d.message||JSON.stringify(d);$('gpuResult').style.color=d.ok?'#b3ff92':'#ff8c9f'}catch(e){$('gpuResult').textContent=e.message}}
function renderNav(){ $('sideLabs').innerHTML=labs.map(l=>`<button class="side-lab ${l.id===current?'active':''}" data-lab="${l.id}"><b>${String(l.id).padStart(2,'0')}</b><span>${escapeHTML(l.name)}</span></button>`).join('');$('sideLabs').querySelectorAll('button').forEach(b=>b.onclick=()=>choose(Number(b.dataset.lab)))}
function rangeFor(n){return n<=6?'1-6':n===7?'7':n===8?'8':n===9?'9':'10-18'}
function choose(n){current=n;renderNav();let lab=labs.find(l=>l.id===n);if(!lab)return;history.replaceState({},'',`/sentinel?lab=${n}`);$('sectionTag').textContent=`LAB ${String(n).padStart(2,'0')} · ${escapeHTML(lab.category||'INTERACTIVE DATABASE')}`;$('sectionTitle').textContent=n===10?'Multi-Document ACID Bank Transfer':lab.name;$('sectionDesc').textContent=n===10?'Execute real debit, credit and audit logging inside a MongoDB transaction.':lab.subtitle;$('reference').href=lab.reference||'#';$('bankView').classList.toggle('hidden',n!==10);$('lab11View').classList.toggle('hidden',n!==11);$('lab12View').classList.toggle('hidden',n!==12);$('lab13View').classList.toggle('hidden',n!==13);$('lab14View').classList.toggle('hidden',n!==14);$('lab15View').classList.toggle('hidden',n!==15);$('lab16View').classList.toggle('hidden',n!==16);$('lab17View').classList.toggle('hidden',n!==17);$('lab18View').classList.toggle('hidden',n!==18);$('genericView').classList.toggle('hidden',n===10||n===11||n===12||n===13||n===14||n===15||n===16||n===17||n===18);document.querySelectorAll('.chapters button').forEach(b=>b.classList.toggle('selected',b.dataset.group===rangeFor(n)));if(n===10){loadBank();return}if(n===11){renderShardLab();return}if(n===12){loadLab12();return}if(n===13){loadLab13();return}if(n===14){loadLab14();return}if(n===15){loadLab15();return}if(n===16){loadLab16();return}if(n===17){loadLab17();return}if(n===18){loadLab18();return}renderGeneric(lab);}
function renderGeneric(lab){$('genericTitle').textContent=`Lab ${current} · ${lab.name}`;$('genericSub').textContent=lab.activities?.map(x=>x.title).join(' · ')||lab.subtitle;const f=forms[current];$('forms').innerHTML=f?`<form id="labForm"><div class="action-form">${f.fields.map(([id,label,example])=>`<label class="${id==='text'?'wide':''}">${escapeHTML(label)}<input name="${id}" placeholder="${escapeHTML(example)}" value="${escapeHTML(example)}" required></label>`).join('')}</div><div class="inline"><button class="btn success" type="submit">${escapeHTML(f.label)} ↗</button></div></form>`:`<p class="fine">This lab uses measured experiments and infrastructure diagnostics. Actions below query the real connected system. Operations needing extra infrastructure report what is missing.</p>`;if(f)$('labForm').onsubmit=async e=>{e.preventDefault();await modelCommand(f.op,Object.fromEntries(new FormData(e.currentTarget).entries()))};let available=labActions.find(x=>x.id===current)?.actions||[];$('labActions').innerHTML=available.map((a,i)=>`<button data-id="${escapeHTML(a.id)}"><b>${String(i+1).padStart(2,'0')} · ${escapeHTML(a.label)}</b> ↗</button>`).join('');$('labActions').querySelectorAll('button').forEach(b=>b.onclick=()=>experiment(b.dataset.id));$('genericResult').textContent='[Ready] Lab selected. Run a command to inspect the real result.';loadDocs()}
async function modelCommand(operation,data){$('genericResult').textContent='[Running] Writing to MongoDB…';try{let d=await api('/api/models/command',request({lab:current,operation,data}));$('genericResult').textContent=JSON.stringify(d,null,2).slice(0,6000);await loadDocs()}catch(e){$('genericResult').textContent='[ERROR] '+e.message}}
async function experiment(action){$('genericResult').textContent='[Running] Executing a live lab experiment…';try{let d=await api('/api/workbench/run',request({lab:current,action}));$('genericResult').textContent=JSON.stringify(d,null,2).slice(0,9000);await loadDocs()}catch(e){$('genericResult').textContent='[ERROR] '+e.message}}
async function loadDocs(){try{let query=new URLSearchParams({q:$('searchDocs').value,limit:'30'});let d=await api(`/api/models/${current}?${query}`);if(!d.ok)throw Error(d.message);$('documentInfo').textContent=`${d.total} live records · ${d.database}${d.collection?'.'+d.collection:''}`;let rows=d.rows||[];if(!rows.length){$('documents').innerHTML='<p class="fine">No documents in this view. Try one of the live actions.</p>';return}let keys=[...new Set(rows.flatMap(x=>Object.keys(x)))].slice(0,6);$('documents').innerHTML=`<table><thead><tr>${keys.map(k=>`<th>${escapeHTML(k)}</th>`).join('')}</tr></thead><tbody>${rows.slice(0,30).map(x=>`<tr>${keys.map(k=>`<td title="${escapeHTML(JSON.stringify(x[k]))}">${escapeHTML(typeof x[k]==='object'?JSON.stringify(x[k]):x[k])}</td>`).join('')}</tr>`).join('')}</tbody></table>`}catch(e){$('documentInfo').textContent='Database unavailable: '+e.message;$('documents').innerHTML=''}}

// Lab 11 is an explicitly labelled shard-routing model, not a claim of live cluster statistics.
// The deterministic workload is calculated in the browser; no database writes occur.
const SHARD_COUNT=3, MODEL_COUNT=100000;
let shardDistribution=null;
function shardHash(str){let h=2166136261;for(let i=0;i<str.length;i++){h=Math.imul(h^str.charCodeAt(i),16777619)}return h>>>0}
function modelShard(key,i){
  const tenant='tenant-'+String((i*37)%103).padStart(3,'0');
  const customer='customer-'+String((i*17)%1009).padStart(4,'0');
  if(key==='hashed_tenant')return shardHash(tenant)%SHARD_COUNT;
  if(key==='hashed_customer')return shardHash(customer)%SHARD_COUNT;
  if(key==='ranged_date')return i<4500?0:i<8500?1:2; // increasing date values: latest inserts to highest range
  // A ranged customer key and skewed customer workload: many orders for hot customer IDs.
  return i%10<6?0:i%10<9?1:2;
}
async function analyzeShards(){
  if($('shardKey').value.startsWith('live_'))return analyzeLiveShards();
  const key=$('shardKey').value;
  $('analyzeShards').disabled=true;
  $('shardModelState').textContent='CALCULATING…';
  requestAnimationFrame(()=>setTimeout(()=>{
    const counts=[0,0,0];
    for(let i=0;i<MODEL_COUNT;i++)counts[modelShard(key,i)]++;
    let chunks=[0,0,0];for(let i=0;i<24;i++)chunks[modelShard(key,Math.floor((i+.5)*MODEL_COUNT/24))]++;
    const max=Math.max(...counts),min=Math.min(...counts),hasHotspot=max/MODEL_COUNT>.55;
    shardDistribution={key,counts,chunks,hasHotspot};
    $('shardCards').innerHTML=counts.map((n,i)=>{const pct=n*100/MODEL_COUNT,hot=n/MODEL_COUNT>.55;return `<div class="shard-card ${hot?'shard-hot':''}"><div class="shard-card-head"><strong>shard0${i+1} <small>(rsShard0${i+1})</small></strong><span>${chunks[i]} modeled chunks</span></div><div class="shard-value">${n.toLocaleString()} docs <span>(${pct.toFixed(1)}%)</span></div><div class="shard-track"><div class="shard-bar ${hot?'hot':''}" style="width:${pct}%"></div></div><div class="shard-card-foot">Status: <strong class="${hot?'hot-label':'balance-label'}">${hot?'HOTSPOT':hasHotspot?'Underutilized':'Balanced'}</strong></div></div>`}).join('');
    const text=key==='ranged_date'?'A monotonically increasing order_date key concentrates recent inserts on the shard owning the upper key range. This demonstrates a write hotspot.':key==='ranged_customer'?'A ranged customer_id key can suffer skew when high-traffic customers fall into particular key ranges. Equality queries can still be targeted.':'Hashed shard keys spread writes across modeled shards. Equality queries that include the shard key can target a shard; range predicates on a hashed key generally scatter.';
    $('shardInsight').classList.toggle('alert',hasHotspot);
    $('shardInsight').innerHTML=`<span class="insight-icon">${hasHotspot?'⚠':'✓'}</span><span><strong>${hasHotspot?'Write hotspot detected':'Balanced distribution'} · ${(max/MODEL_COUNT*100).toFixed(1)}% on busiest shard.</strong> ${escapeHTML(text)}</span>`;
    $('shardModelState').textContent='CALCULATED · LOCAL MODEL';
    routeShard();
    $('analyzeShards').disabled=false;
  },25));
}
async function analyzeLiveShards(){
 const key=$('shardKey').value, collection=key==='live_even'?'even_data':'hotspot_data';
 $('analyzeShards').disabled=true;$('shardModelState').textContent='READING LIVE MONGOS…';
 try{
  const d=await api('/api/sentinel/lab11/live?collection='+encodeURIComponent(collection));
  if(!d.ok)throw Error(d.message||'Live cluster unavailable');
  const total=d.total||1, max=Math.max(...d.shards.map(s=>s.documents));
  const hasHotspot=max/total>.8;
  shardDistribution={key,live:true,hasHotspot};
  $('shardCards').innerHTML=d.shards.map(s=>{const pct=100*s.documents/total,hot=pct>80;return `<div class="shard-card ${hot?'shard-hot':''}"><div class="shard-card-head"><strong>${escapeHTML(s.name)}</strong><span>${s.chunks} REAL chunks</span></div><div class="shard-value">${s.documents.toLocaleString()} docs <span>(${pct.toFixed(1)}%)</span></div><div class="shard-track"><div class="shard-bar ${hot?'hot':''}" style="width:${pct}%"></div></div><div class="shard-card-foot">Status: <strong class="${hot?'hot-label':'balance-label'}">${hot?'HOTSPOT':hasHotspot?'UNDERUTILIZED':'Balanced'}</strong></div></div>`}).join('');
  $('shardModelState').textContent=`LIVE MONGOS · ${d.shards.length} SHARDS · ${d.chunk_count} CHUNKS`;
  $('shardInsight').classList.toggle('alert',hasHotspot);
  $('shardInsight').innerHTML=`<span class="insight-icon">${hasHotspot?'⚠':'✓'}</span><span><strong>${hasHotspot?'Live hotspot detected':'Live balanced distribution'}: ${max.toLocaleString()} / ${d.total.toLocaleString()} records (${(100*max/total).toFixed(1)}%) on busiest shard.</strong> Source: ${escapeHTML(d.collection)} via mongos, actual shard and chunk metadata. No artificial third shard; no fake query timings.</span>`;
  routeShard();
 }catch(e){$('shardModelState').textContent='LIVE CONNECTION ERROR';$('shardCards').innerHTML=`<div class="shard-placeholder">${escapeHTML(e.message)}. Verify Docker mongos exposes localhost:27517.</div>`}
 finally{$('analyzeShards').disabled=false}
}
function routeShard(){
  const key=$('shardKey').value, query=$('shardQuery').value;
  const hashed=key.startsWith('hashed')||key==='live_even';
  const targeted=query==='equality'||(query==='range'&&!hashed);
  const heading=targeted?'Targeted shard routing':'Scatter-gather routing';
  let detail= query==='equality'?'Equality on the complete shard key can identify one owning shard.':query==='other'?'Without a shard-key predicate, mongos generally broadcasts to all shards.':hashed?'A range filter on the original value of a hashed shard key cannot normally map to a contiguous shard-key range.':'A range query on a ranged shard key can prune shards based on chunk boundaries, but may span more than one shard.';
  if(query==='range'&&!hashed)detail='Ranged shard-key predicates can restrict routing to matching chunks, potentially on one or several shards. Actual targeting depends on chunk boundaries.';
  $('shardRouteOutput').innerHTML=`<span class="route-indicator ${targeted?'target':'scatter'}">${targeted?'◉':'◎'}</span><div><strong>${heading}</strong><p>${escapeHTML(detail)} ${shardDistribution?.live?'The shard cards report actual documents and chunks, but these routing conclusions are conceptual; no explain() was run.':shardDistribution?'The three distribution cards show modeled writes, not measured query latency.':'Run Analyze Shard Routing for distribution.'}</p></div>`;
}
function renderShardLab(){
  $('sectionTitle').textContent='Horizontal Sharding & Chunk Routing';
  $('sectionDesc').textContent='Live data from the existing two-shard mongos cluster, with an optional three-shard simulation';
  $('shardModelState').textContent=shardDistribution?'CALCULATED · LOCAL MODEL':'READY TO ANALYZE';
}


// Lab 12: real MongoDB $jsonSchema validation; no simulated database commits.
let lab12Running=false;
function lab12Tile(id,title,pass,detail){
 let el=$(id);el.classList.toggle('valid',Boolean(pass));el.classList.toggle('invalid',!pass);
 el.querySelector('strong').textContent=(pass?'PASS':'FAIL')+' ('+detail+')';
}
async function runLab12(e){
 if(e)e.preventDefault();if(lab12Running)return;lab12Running=true;$('lab12Run').disabled=true;
 const payload={email:$('lab12Email').value,age:Number($('lab12Age').value),severity:$('lab12Severity').value};
 $('lab12Message').textContent='[MongoDB] Executing insert with enforced collection validator…';
 try{
  const data=await api('/api/sentinel/lab12/validate',request(payload));
  lab12Tile('lab12EmailStatus','email',data.checks?.email,'format');
  lab12Tile('lab12AgeStatus','age',data.checks?.age,String(payload.age)+' years');
  lab12Tile('lab12SeverityStatus','severity',data.checks?.severity,payload.severity);
  let status=$('lab12MongoStatus');status.classList.toggle('valid',!!data.committed);status.classList.toggle('invalid',!data.committed);
  status.querySelector('strong').textContent=data.committed?'COMMITTED TO LAB_12':data.ok?'REJECTED BY SCHEMA':'DATABASE ERROR';
  $('lab12Message').textContent='['+(data.committed?'COMMIT':data.ok?'VALIDATION REJECTED':'ERROR')+'] '+data.message;
  if(data.committed)await loadLab12Records();
 }catch(ex){$('lab12Message').textContent='[ERROR] '+ex.message}
 finally{lab12Running=false;$('lab12Run').disabled=false}
}
async function loadLab12Records(){
 try{
 let data=await api('/api/sentinel/lab12/records');
 if(!data.ok)throw Error(data.message);
 let rows=data.records||[];
 $('lab12Records').innerHTML=rows.length?'<table><thead><tr><th>Email</th><th>Age</th><th>Severity</th><th>Saved (UTC)</th></tr></thead><tbody>'+rows.map(r=>'<tr><td>'+escapeHTML(r.email)+'</td><td>'+escapeHTML(r.age)+'</td><td>'+escapeHTML(r.severity)+'</td><td>'+escapeHTML((r.created_at||'').replace('T',' ').slice(0,19))+'</td></tr>').join('')+'</tbody></table>':'No records committed yet. Run a valid schema submission.';
 }catch(ex){$('lab12Records').textContent='Unable to load validation records: '+ex.message}
}
function loadLab12(){loadLab12Records();let acts=labActions.find(l=>l.id===12)?.actions||[];
 $('lab12ExtraActions').innerHTML=acts.map(a=>'<button type="button" data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab12ExtraActions').querySelectorAll('button').forEach(btn=>btn.onclick=async()=>{
  $('lab12ExtraResult').textContent='Running security diagnostic…';
  try{let d=await api('/api/workbench/run',request({lab:12,action:btn.dataset.id}));$('lab12ExtraResult').textContent=JSON.stringify(d,null,2).slice(0,6000)}catch(ex){$('lab12ExtraResult').textContent='Error: '+ex.message}
 });
}


// Lab 13: real MongoDB read-only projection view. App-side role preview != authenticated RBAC.
let lab13Busy=false;
async function lab13Inspect(){
 if(lab13Busy)return;lab13Busy=true;$('lab13Inspect').disabled=true;
 $('lab13Result').textContent='[MongoDB] Querying analyst projection…';
 try{
  let data=await api('/api/sentinel/lab13/projection?role='+encodeURIComponent($('lab13Role').value));
  if(!data.ok)throw Error(data.message||'MongoDB query failed');
  $('lab13MongoStatus').textContent='MONGODB · CONNECTED';$('lab13ViewStatus').textContent='VIEW · '+(data.view_exists?'ACTIVE':'NOT FOUND');
  $('lab13Rows').innerHTML=(data.records||[]).map(r=>'<tr><td class="lab13-accent">'+escapeHTML(r.analyst_id)+'</td><td>'+escapeHTML(r.name)+'</td><td>'+escapeHTML(r.clearance)+'</td><td class="lab13-privacy">'+escapeHTML(r.gov_id_display)+'</td><td>'+escapeHTML(r.api_token_display)+'</td></tr>').join('')||'<tr><td colspan="5">No records found</td></tr>';
  $('lab13Result').textContent='[VIEW] '+data.message+' · Database: '+data.database+' · Source: '+data.source;
 }catch(e){$('lab13Result').textContent='[ERROR] '+e.message;$('lab13MongoStatus').textContent='MONGODB · ERROR'}
 finally{lab13Busy=false;$('lab13Inspect').disabled=false}
}
async function lab13WriteTest(){
 $('lab13Result').textContent='[MongoDB] Attempting a harmless insert into read-only view…';
 try{let d=await api('/api/sentinel/lab13/view-write-test',{method:'POST'});$('lab13Result').textContent='['+(d.ok?'PASS':'ERROR')+'] '+d.message+' (MongoDB code: '+(d.code??'n/a')+')'}
 catch(e){$('lab13Result').textContent='[ERROR] '+e.message}
}
function loadLab13(){lab13Inspect();let acts=labActions.find(x=>x.id===13)?.actions||[];
 $('lab13ExtraActions').innerHTML=acts.map(a=>'<button type="button" data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab13ExtraActions').querySelectorAll('button').forEach(b=>b.onclick=async()=>{
  $('lab13ExtraResult').textContent='Checking real deployment environment…';
  try{let d=await api('/api/workbench/run',request({lab:13,action:b.dataset.id}));$('lab13ExtraResult').textContent=JSON.stringify(d,null,2).slice(0,6500)}
  catch(e){$('lab13ExtraResult').textContent='Error: '+e.message}
 });
}


// Lab 14: actual serverStatus counters, a clearly labeled cache proxy and safe snapshots.
let lab14Busy=false;
async function lab14Evaluate(){
 if(lab14Busy)return;lab14Busy=true;$('lab14Evaluate').disabled=true;
 const threshold=Number($('lab14Threshold').value);
 $('lab14Result').textContent='[MongoDB] Reading serverStatus counters…';
 try{
  const d=await api('/api/sentinel/lab14/telemetry?threshold='+encodeURIComponent(threshold));
  if(!d.ok)throw Error(d.message);
  const c=d.connections||{};
  $('lab14Connections').textContent=(c.current??'—')+' / '+(c.available??'—');
  $('lab14ConnectionNote').textContent='Current / available connections';
  $('lab14Hit').textContent=d.cache_hit_proxy_pct==null?'N/A':d.cache_hit_proxy_pct.toFixed(1)+'%';
  $('lab14Sla').textContent=threshold+'%';
  $('lab14SlaNote').textContent=d.cache_hit_proxy_pct==null?'Counters unavailable':'Proxy comparison only';
  const flag=d.sla_status==='PROXY ABOVE THRESHOLD';
  $('lab14Alert').textContent=d.cache_hit_proxy_pct==null?'UNKNOWN':flag?'PROXY OK':'PROXY BELOW';
  $('lab14Alert').classList.toggle('lab14-low',!flag);
  $('lab14Result').textContent='[LIVE] '+d.message+' | Requested pages: '+(d.wired_tiger?.pages_requested??'n/a')+', pages read into cache: '+(d.wired_tiger?.pages_read_into_cache??'n/a')+' | Updated: '+d.measured_at;
 }catch(e){$('lab14Result').textContent='[ERROR] '+e.message;$('lab14Alert').textContent='ERROR'}
 finally{lab14Busy=false;$('lab14Evaluate').disabled=false}
}
async function lab14Snapshot(url,method){$('lab14BackupResult').textContent='[MongoDB] Processing snapshot operation…';try{
 const d=await api(url,{method});$('lab14BackupResult').textContent=JSON.stringify(d,null,2);
 }catch(e){$('lab14BackupResult').textContent='[ERROR] '+e.message}}
async function loadLab14(){
 $('lab14Result').textContent='[Ready] Reading live MongoDB metrics from the dedicated Lab 14 panel.';
 const acts=labActions.find(x=>x.id===14)?.actions||[];
 $('lab14ExtraActions').innerHTML=acts.map(a=>'<button data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab14ExtraActions').querySelectorAll('button').forEach(b=>b.onclick=async()=>{
  $('lab14ExtraResult').textContent='[Running] Original Lab 14 action…';
  try{let d=await api('/api/workbench/run',request({lab:14,action:b.dataset.id}));$('lab14ExtraResult').textContent=JSON.stringify(d,null,2)}catch(e){$('lab14ExtraResult').textContent='[ERROR] '+e.message}
 });
 await lab14Evaluate();
}


// Lab 15: real, isolated MongoDB tenant task collections and migration.
let lab15Busy=false;
function lab15Chosen(){return {tenant:$('lab15Tenant').value,strategy:$('lab15Strategy').value}}
async function lab15Fetch(){
 const v=lab15Chosen();
 try{
  let d=await api('/api/sentinel/lab15/state?'+new URLSearchParams(v));
  if(!d.ok)throw Error(d.message||'MongoDB unavailable');
  $('lab15Type').textContent=v.strategy==='shared'?'Shared Pool':'Collection per Tenant';
  $('lab15Namespace').textContent=d.namespace.split('.').pop();
  $('lab15Count').textContent=Number(d.count).toLocaleString();
  $('lab15Other').textContent='Shared: '+d.shared_count+' · Isolated: '+d.isolated_count;
  $('lab15TaskSource').textContent=d.namespace;
  $('lab15Rows').innerHTML=d.tasks.length?d.tasks.map(r=>'<tr><td>'+escapeHTML(r.task_id)+'</td><td>'+escapeHTML(r.title)+'</td><td>'+escapeHTML(r.tenant_id||v.tenant)+'</td><td>'+escapeHTML(r.priority)+'</td><td>'+escapeHTML(r.status)+'</td></tr>').join(''):'<tr><td colspan="5">No tasks in this collection yet. Seed or create a task.</td></tr>';
 }catch(e){$('lab15Message').textContent='[ERROR] '+e.message}
}
async function lab15Action(kind){
 if(lab15Busy)return;lab15Busy=true;
 const btns=['lab15Create','lab15Seed','lab15Migrate','lab15Compare','lab15Refresh'].map(id=>$(id));btns.forEach(b=>b.disabled=true);
 $('lab15Message').textContent='[MongoDB] Running '+kind+'…';
 try{
  let d;
  if(kind==='create'){
   const title=$('lab15Title').value.trim();if(!title)throw Error('Enter a task title');
   d=await api('/api/sentinel/lab15/create',request({tenant:$('lab15Tenant').value,title,priority:$('lab15Priority').value}));
   $('lab15Rate').textContent=d.rate_limited?'LIMIT REACHED — '+d.message:(d.ok?'Used '+d.used+' of '+d.limit+' creates in the current window.':'Error: '+d.message);
  }else if(kind==='seed')d=await api('/api/sentinel/lab15/seed',{method:'POST'});
  else if(kind==='migrate')d=await api('/api/sentinel/lab15/migrate',{method:'POST'});
  else if(kind==='benchmark'){
   d=await api('/api/sentinel/lab15/benchmark?tenant='+encodeURIComponent($('lab15Tenant').value));
   if(d.ok){$('lab15Latency').textContent=(d.median_ms[$('lab15Strategy').value]??'—')+' ms';}
  }else {await lab15Fetch();$('lab15Message').textContent='[LIVE] Tenant data refreshed.';return}
  $('lab15Message').textContent='['+(d.ok?'LIVE':'NOTICE')+'] '+(d.message||d.note||'Result received')+(d.results?' '+JSON.stringify(d.results):'')+(d.median_ms?' '+JSON.stringify(d.median_ms):'');
  await lab15Fetch();
 }catch(e){$('lab15Message').textContent='[ERROR] '+e.message}
 finally{lab15Busy=false;btns.forEach(b=>b.disabled=false)}
}
async function loadLab15(){
 $('lab15Message').textContent='[Ready] Live MongoDB tenant dashboard.';
 const acts=labActions.find(x=>x.id===15)?.actions||[];
 $('lab15ExtraActions').innerHTML=acts.map(a=>'<button data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab15ExtraActions').querySelectorAll('button').forEach(b=>b.onclick=async()=>{
  $('lab15ExtraResult').textContent='Running original lab command…';
  try{const d=await api('/api/workbench/run',request({lab:15,action:b.dataset.id}));$('lab15ExtraResult').textContent=JSON.stringify(d,null,2)}
  catch(e){$('lab15ExtraResult').textContent='[ERROR] '+e.message}
 });
 await lab15Fetch();
}


// Lab 16: real polyglot service executed inside the existing lab16 Docker app.
let lab16Busy=false;
function lab16Status(id,value,ok){const el=$(id);el.textContent=value;el.style.color=ok===true?'#8af6b5':ok===false?'#ffae7d':'#c4d5e6'}
function lab16Loading(b){lab16Busy=b;$('lab16Run').disabled=b;$('lab16Circuit').disabled=b}
async function loadLab16(){
 $('lab16Log').textContent='[LIVE] Looking up seeded transactions in the Lab 16 Docker application…';
 try{const d=await api('/api/sentinel/lab16/transactions');if(!d.ok)throw Error(d.message);
   $('lab16Txn').innerHTML=d.transactions.map(t=>'<option value="'+escapeHTML(t.txn_id)+'">'+escapeHTML(t.txn_id+' — '+(t.merchant||'Transaction')+' ($'+Number(t.amount||0).toLocaleString()+') | Risk '+Number(t.risk_score||0).toFixed(2))+'</option>').join('');
   $('lab16Log').textContent='[LIVE] '+d.transactions.length+' real transaction(s) loaded. Choose a transaction and run analysis.';
 }catch(e){$('lab16Txn').innerHTML='<option value="">Lab 16 Docker unavailable</option>';$('lab16Log').textContent='[NOT CONNECTED] '+e.message+'\nStart Lab 16 containers and seed them; no fake data will be shown.'}
 let acts=labActions.find(x=>x.id===16)?.actions||[];
 $('lab16ExtraActions').innerHTML=acts.map(a=>'<button data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab16ExtraActions').querySelectorAll('button').forEach(b=>b.onclick=async()=>{try{const d=await api('/api/workbench/run',request({lab:16,action:b.dataset.id}));$('lab16ExtraResult').textContent=JSON.stringify(d,null,2)}catch(e){$('lab16ExtraResult').textContent=e.message}})
}
async function runLab16(){if(lab16Busy)return;const txn=$('lab16Txn').value;if(!txn){$('lab16Log').textContent='[ERROR] No live transaction available; start the Lab 16 Docker stack.';return}lab16Loading(true);$('lab16Log').textContent='[LIVE] Querying three databases through FraudQueryService…';
 try{const d=await api('/api/sentinel/lab16/analyze',request({txn_id:txn}));if(!d.ok)throw Error(d.message);const v=d.result, t=v.transaction, ev=v.recent_events||[], graph=v.related_accounts||[], errors=v.errors||{};
 lab16Status('lab16MongoState',errors.mongo?'ERROR':'CONNECTED',!errors.mongo);$('lab16MongoMain').textContent=t?(t.merchant||t.txn_id)+' — $'+Number(t.amount||0).toLocaleString():'No matching transaction';$('lab16MongoDetails').textContent=t?'Account '+t.user_id+' · Transaction '+t.txn_id:'MongoDB did not return a transaction';$('lab16MongoLatency').textContent='Query '+(v.latency_ms?.mongo??'—')+' ms';
 lab16Status('lab16CassandraState',errors.cassandra?'ERROR':'CONNECTED',!errors.cassandra);$('lab16CassandraMain').textContent=errors.cassandra?'Backend unavailable':ev.length+' recorded event(s)';$('lab16CassandraDetails').textContent=ev.length?ev.slice(0,3).map(x=>x.txn_id+' ($'+x.amount+')').join(' · '):'No recorded events';$('lab16CassandraLatency').textContent='Query '+(v.latency_ms?.cassandra??'—')+' ms';
 lab16Status('lab16Neo4jState',errors.neo4j?'ERROR':'CONNECTED',!errors.neo4j);$('lab16Neo4jMain').textContent=errors.neo4j?'Backend unavailable':graph.length+' related account(s)';$('lab16Neo4jDetails').textContent=graph.length?graph.slice(0,5).map(x=>x.related_user+' ('+x.hops+' hop)').join(' · '):'No connections found within 2 hops';$('lab16Neo4jLatency').textContent='Query '+(v.latency_ms?.neo4j??'—')+' ms';
 const risk=t?Number(t.risk_score||0):null;$('lab16Risk').textContent=risk===null?'UNKNOWN':risk.toFixed(2);$('lab16Verdict').textContent=risk===null?'No score available':risk>=.8?'HIGH RISK · REVIEW / ESCALATE':risk>=.5?'MEDIUM RISK · REVIEW':'LOW RISK · MONITOR';
 $('lab16Log').textContent='[LIVE] '+txn+' analysis complete.\nSource: '+d.source+'\n'+(Object.keys(errors).length?'BACKEND ERRORS: '+JSON.stringify(errors):'All three database queries returned without connection errors.')+'\nMeasured query latencies (ms): '+JSON.stringify(v.latency_ms);
 }catch(e){$('lab16Log').textContent='[ERROR] '+e.message}finally{lab16Loading(false)}
}
async function testLab16Circuit(){if(lab16Busy)return;lab16Loading(true);try{const d=await api('/api/sentinel/lab16/circuit-test',{method:'POST'});if(!d.ok)throw Error(d.message);$('lab16Log').textContent='[SIMULATED FAILURE INJECTION / REAL CIRCUITBREAKER CLASS]\n'+d.steps.join('\n')+'\n'+d.note;lab16Status('lab16Neo4jState','SIMULATED OPEN',false)}catch(e){$('lab16Log').textContent='[ERROR] '+e.message}finally{lab16Loading(false)}}


// Lab 17: real Lab 17 Docker embeddings / MongoDB and measured local FAISS benchmarks.
let lab17Busy=false;
function lab17BusySet(on){lab17Busy=on;['lab17Search','lab17Answer','lab17Seed','lab17Benchmark'].forEach(id=>$(id).disabled=on)}
function lab17RenderResults(results){
 $('lab17Results').innerHTML=(results||[]).length?results.map((r,i)=>`<article class="lab17-result"><div class="lab17-result-head"><strong>#${i+1} · ${escapeHTML(r.source||'Stored passage')}</strong><span>${Number(r.score||0).toFixed(4)}</span></div><p>${escapeHTML(r.text||'')}</p></article>`).join(''):'<div class="lab17-empty">No matching stored passages. Seed the local Lab 17 MongoDB corpus.</div>';
}
async function lab17Call(endpoint,body){
 if(lab17Busy)return;lab17BusySet(true);$('lab17Log').textContent='[RUNNING] '+(body?.query||endpoint);
 try{const d=await api(endpoint,body?request(body):undefined);if(!d.ok)throw Error(d.message||'Operation failed');
  if(d.results){lab17RenderResults(d.results);$('lab17Source').textContent='LIVE · '+(d.source||'Lab 17 Docker')+' · '+(d.embedding_model||'384-dimensional local embedding')+' · '+(d.elapsed_ms??'—')+' ms';}
  if(d.answer){$('lab17Response').textContent='['+(d.generation||'retrieval')+']\n'+d.answer+'\nPrevious messages used: '+(d.previous_messages_used??0);if(d.top_chunks)lab17RenderResults(d.top_chunks)}
  if(d.seeded){$('lab17Source').textContent='SEEDED · '+d.seeded+' real passages · '+d.embedding_model+' · '+d.dimensions+' dimensions'}
  if(d.benchmarks){$('lab17BenchRows').innerHTML=d.benchmarks.map(r=>`<tr><td><strong>${escapeHTML(r.index)}</strong> · ${escapeHTML(r.parameters)}</td><td>${Number(r.avg_latency_ms).toFixed(3)} ms</td><td>${Number(r.recall_at_20_pct).toFixed(2)}%</td><td>${Number(r.build_seconds).toFixed(3)} s</td></tr>`).join('');$('lab17Source').textContent='MEASURED · '+d.benchmarks.length+' FAISS configurations · '+d.benchmark_description;}
  $('lab17Log').textContent='[SUCCESS] '+(d.message||d.source||d.benchmark_description||'Operation complete')+'\n'+(d.notes||'');
 }catch(e){$('lab17Log').textContent='[ERROR] '+e.message+'\nStart the Lab 17 Docker project and seed its MongoDB corpus. No sample scores are substituted.'}
 finally{lab17BusySet(false)}
}
async function lab17SearchRun(){const q=$('lab17Query').value.trim();if(!q){$('lab17Log').textContent='Enter a question';return}await lab17Call('/api/sentinel/lab17/search',{query:q})}
async function lab17AnswerRun(){const q=$('lab17Query').value.trim();if(!q){$('lab17Log').textContent='Enter a question';return}await lab17Call('/api/sentinel/lab17/answer',{query:q,user_id:'sentinel-student'})}
async function loadLab17(){
 $('sectionTitle').textContent='Vector Search RAG & HNSW/IVF';$('sectionDesc').textContent='Live threat passage retrieval and measured local vector-index comparisons';
 try{let d=await api('/api/sentinel/lab17/status');$('lab17Source').textContent=d.ok?'CONNECTED · '+d.documents+' stored chunks · '+(d.embedding_model||'local embeddings'):'DISCONNECTED · '+d.message}
 catch(e){$('lab17Source').textContent='DISCONNECTED · '+e.message}
 const acts=labActions.find(l=>l.id===17)?.actions||[];
 $('lab17ExtraActions').innerHTML=acts.map(a=>'<button data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab17ExtraActions').querySelectorAll('button').forEach(b=>b.onclick=async()=>{try{const d=await api('/api/workbench/run',request({lab:17,action:b.dataset.id}));$('lab17ExtraResult').textContent=JSON.stringify(d,null,2)}catch(e){$('lab17ExtraResult').textContent=e.message}});
}

async function init(){try{const [catalog,workbench]=await Promise.all([api('/api/labs'),api('/api/workbench/labs')]);labs=catalog.labs||[];labActions=workbench.labs||[];}catch(e){$('connection').textContent='Backend offline: '+e.message;return} $('lab12Form').onsubmit=runLab12;$('lab12Refresh').onclick=loadLab12Records;$('lab13Inspect').onclick=lab13Inspect;$('lab13WriteTest').onclick=lab13WriteTest;$('lab14Evaluate').onclick=lab14Evaluate;$('lab14Refresh').onclick=lab14Evaluate;$('lab14Backup').onclick=()=>lab14Snapshot('/api/sentinel/lab14/backup','POST');$('lab14Verify').onclick=()=>lab14Snapshot('/api/sentinel/lab14/verify','GET');$('lab15Create').onclick=()=>lab15Action('create');$('lab15Seed').onclick=()=>lab15Action('seed');$('lab15Migrate').onclick=()=>lab15Action('migrate');$('lab15Compare').onclick=()=>lab15Action('benchmark');$('lab15Refresh').onclick=()=>lab15Action('refresh');$('lab16Txn').onchange=()=>{$('lab16Log').textContent='[Ready] Select Run Polyglot FraudQueryService to analyze the chosen live record.'};$('lab16Run').onclick=runLab16;$('lab16Circuit').onclick=testLab16Circuit;$('lab17Search').onclick=lab17SearchRun;$('lab17Answer').onclick=lab17AnswerRun;$('lab17Seed').onclick=()=>lab17Call('/api/sentinel/lab17/seed',{});$('lab17Benchmark').onclick=()=>lab17Call('/api/sentinel/lab17/benchmark',{});$('lab18Analyze').onclick=lab18Analyze;$('lab15Tenant').onchange=lab15Fetch;$('lab15Strategy').onchange=lab15Fetch;$('analyzeShards').onclick=analyzeShards;$('routeShard').onclick=routeShard;$('shardKey').onchange=()=>{shardDistribution=null;$('shardModelState').textContent='CHANGED · RUN ANALYSIS';$('shardCards').innerHTML='<div class="shard-placeholder">Click Analyze Shard Routing to calculate the selected distribution.</div>';routeShard()};$('shardQuery').onchange=routeShard;$('resetBank').onclick=resetBank;$('validTransfer').onclick=()=>runTransfer();$('failureTransfer').onclick=()=>runTransfer({amount:2000});$('rollbackTransfer').onclick=()=>runTransfer({amount:1,test_failure:true});$('refreshBank').onclick=loadBank;$('initGpu').onclick=()=>inventory('init');$('reserveGpu').onclick=()=>inventory('reserve');$('refreshDocs').onclick=loadDocs;$('searchDocs').onkeydown=e=>{if(e.key==='Enter')loadDocs()};$('overviewBtn').onclick=()=>choose(18);document.querySelectorAll('.chapters button').forEach(b=>b.onclick=()=>choose(({overview:18,'1-6':4,'7':7,'8':8,'9':9,'10-18':10})[b.dataset.group]));choose(Math.max(1,Math.min(18,Number(new URLSearchParams(location.search).get('lab'))||10)))}
init();

// Lab 18-only: always renders actual MongoDB counts and saved measured CSV data.
const lab18Fmt=n=>Number(n).toLocaleString('en-US');
async function lab18Analyze(){
 const button=$('lab18Analyze');button.disabled=true;button.textContent='Analyzing…';
 const query=new URLSearchParams({source:$('lab18Source').value,community:$('lab18Community').value,scale:$('lab18Scale').value});
 try{
  const d=await api('/api/sentinel/lab18/analytics?'+query.toString());
  const selector=$('lab18Source'),old=selector.value;
  const options=['<option value="all">ALL SOURCES</option>',...(d.sources||[]).map(x=>'<option value="'+escapeHTML(x)+'">'+escapeHTML(x)+'</option>')];
  selector.innerHTML=options.join('');selector.value=(d.sources||[]).includes(old)?old:'all';
  const communities=$('lab18Community'),oldCommunity=communities.value;
  communities.innerHTML='<option value="all">ALL THREATS</option><option value="flagged">FLAGGED FALSE-POSITIVE CANDIDATES</option><option value="other">OTHER THREATS</option>'+ (d.graph_groups||[]).map(g=>'<option value="'+escapeHTML(g.id)+'">'+escapeHTML(g.label)+'</option>').join('');
  communities.value=['all','flagged','other',...(d.graph_groups||[]).map(g=>g.id)].includes(oldCommunity)?oldCommunity:'all';
  $('lab18SourceStatus').textContent=d.ok?'● LIVE LAB 18 MONGODB · PORT 27021':'● LAB 18 MONGODB UNAVAILABLE';
  $('lab18Total').textContent=d.total==null?'—':lab18Fmt(d.total);
  $('lab18Matched').textContent=d.matched==null?'—':lab18Fmt(d.matched);
  $('lab18FP').textContent=d.false_positive_candidates==null?'—':lab18Fmt(d.false_positive_candidates);
  $('lab18Latency').textContent=d.ok?Number(d.filter_latency_ms).toFixed(3)+' ms':'—';
  $('lab18Log').textContent=d.ok?'[LIVE] '+d.label+'\n'+d.community_note+'\nSaved graph groups loaded: '+(d.graph_groups||[]).length:'[OFFLINE] '+(d.message||'MongoDB unavailable');
  let plan=d.scale_estimate||{};
  $('lab18ScaleHeading').textContent='HORIZONTAL SCALING BLUEPRINT · '+d.scale_millions+'M RECORDS (~'+plan.raw_data_estimate_gb+' GB RAW)';
  $('lab18MongoPlan').textContent=plan.mongodb||'—';$('lab18CassPlan').textContent=plan.cassandra||'—';$('lab18NeoPlan').textContent=plan.neo4j||'—';
  $('lab18ScaleAssumption').textContent='ILLUSTRATIVE ONLY · '+(plan.assumption||'')+' Excludes replication, indexes, memory, graph edges and backup requirements.';
  const patternLabels={threat_history:'1. Threat History (latest 50 by source)',target_spread:'2. Target & Spread (cross-source target)',daily_volume:'3. Daily Volume Analytics (by day and type)',insert_10_events:'4. Real-Time Insert (10-event batch)'};
  const prefer={threat_history:'MongoDB for current sample',target_spread:'Cassandra for these lookups',daily_volume:'Cassandra for this query',insert_10_events:'Compare throughput across engines'};
  let by={};for(const r of (d.benchmark?.rows||[])){(by[r.pattern]??={})[r.backend]=r;}
  $('lab18BenchRows').innerHTML=Object.entries(patternLabels).map(([pattern,label])=>{let row=by[pattern]||{};let cells=['mongodb','cassandra','neo4j'].map(engine=>{let x=row[engine];if(!x)return '<td>—</td>';let v=Number(x.median_ms);return '<td><strong>'+ (Number.isFinite(v)?v.toFixed(3)+' ms':'—')+'</strong>'+(x.events_per_sec?'<small>'+Number(x.events_per_sec).toLocaleString('en-US')+' events/s</small>':'')+'</td>';});return '<tr><td>'+label+'</td>'+cells.join('')+'<td>'+escapeHTML(prefer[pattern])+'</td></tr>'}).join('');
  $('lab18BenchSource').textContent=(d.benchmark?.source||'No saved benchmark')+' · '+ ((d.benchmark?.rows||[]).length)+' measurements';
  $('lab18RecordRows').innerHTML=(d.latest||[]).length?'<div class="lab18-tablewrap"><table><thead><tr><th>THREAT ID</th><th>SOURCE</th><th>TYPE</th><th>TARGET</th><th>FP LABEL</th></tr></thead><tbody>'+(d.latest||[]).map(x=>'<tr><td>'+escapeHTML(x.threat_id)+'</td><td>'+escapeHTML(x.from_source)+'</td><td>'+escapeHTML(x.threat_type)+'</td><td>'+escapeHTML(x.target)+'</td><td>'+(x.is_false_positive?'Flagged':'Other')+'</td></tr>').join('')+'</tbody></table></div>':'No matching records available.';
 }catch(e){$('lab18Log').textContent='[ERROR] '+e.message;}
 finally{button.disabled=false;button.textContent='▶ Analyze 100K Dataset'}
}
async function loadLab18(){
 $('lab18Source').onchange=lab18Analyze;$('lab18Community').onchange=lab18Analyze;$('lab18Scale').onchange=lab18Analyze;
 const acts=labActions.find(l=>l.id===18)?.actions||[];
 $('lab18ExtraActions').innerHTML=acts.map(a=>'<button data-id="'+escapeHTML(a.id)+'">'+escapeHTML(a.label)+' ↗</button>').join('');
 $('lab18ExtraActions').querySelectorAll('button').forEach(b=>b.onclick=async()=>{try{$('lab18ExtraResult').textContent=JSON.stringify(await api('/api/workbench/run',request({lab:18,action:b.dataset.id})),null,2)}catch(e){$('lab18ExtraResult').textContent=e.message}});
 await lab18Analyze();
}
