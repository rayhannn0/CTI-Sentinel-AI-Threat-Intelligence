from common import save
notes={
 'activity':'Activity 11.1 — MongoDB 5.0+ resharding',
 'steps':[
  'Confirm version, FCV, cluster health, disk headroom, and workload impact; back up data.',
  'Choose a new shard key and ensure an appropriate supporting index when required.',
  'Run db.adminCommand({reshardCollection:"lab11.collection",key:{new_key:1}}) through mongos (or sh.reshardCollection).',
  'MongoDB copies data to temporary recipient collections while capturing concurrent writes.',
  'Monitor currentOp, server logs, and resharding status; allow the coordinator to commit.',
  'Verify shard distribution, routing/explain plans, indexes, and application behavior after completion.'
 ],
 'limitations_and_cautions':[
  'Supported on MongoDB 5.0+ sharded clusters; exact restrictions vary by server version.',
  'Consumes significant CPU, disk, and network resources; plan capacity and a maintenance window.',
  'A brief critical section can block operations during cutover.',
  'Unique index, zone/shard-key, time-series, and collection-type restrictions require version-specific review.',
  'A new key must match actual query patterns; resharding does not make hashed range predicates targeted.',
  'Do not execute reshardCollection on production without checking the MongoDB documentation for your exact version.'
 ],
 'note':'Research summary, not a destructive resharding operation; tested project uses MongoDB 7.0.'}
for x in notes['steps']:print('-',x)
save('activity_11_1.json',notes)
