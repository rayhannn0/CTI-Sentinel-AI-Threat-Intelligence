# Lab 7.1 – production-inspired teaching schema

**Data provenance:** The database is a **synthetic reconstruction** inspired by CTI Digest's aggregation categories, NOT a dump of CTI Digest and NOT a verified record of actual threats.

| Relationship | Design | Why |
| --- | --- | --- |
| threats → tags, observables, mitigations, source_assessment | Embedded | Bounded, commonly read together with the threat |
| threats.source_ids → sources._id | Referenced | Shared source metadata changes independently and can be reused by many threats |
| reports.source_id → sources._id | Referenced | Reports are independent and share source descriptors |

Embedded alternative for threats→sources: `sources_embedded:[{_id,name,url,verification}]`. One document read retrieves source details without `$lookup`; updating name/reputation across threats becomes harder and creates duplication. A source being reputable DOES NOT mean every headline is a verified threat; classification must be based on independently checked evidence.

Lab 7.1 calculates `$bsonSize` average and maximum, with 16 MiB threshold inspection. The lesson demonstrates schema analysis rather than claiming to reconstruct the site's real internal database.

## Working set / cache interpretation

Lab 7.2 creates 100,000 approx 2 KB BSON documents. The `serverStatus.wiredTiger.cache` cache occupancy measures memory usage within WiredTiger's allocated cache, **not** the percent of collection documents in cache. Hit-proxy using cache-requested and pages-read counters is approximate and may be distorted by concurrent workloads; inaccessible metrics are reported gracefully. This must be run against an instance using WiredTiger, with necessary monitoring permissions.

## Source links
- https://ctidigest.com/
- https://github.com/jacobdjwilson/awesome-annual-security-reports
- https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-07
