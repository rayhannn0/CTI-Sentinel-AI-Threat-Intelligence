from common import save
rows=[
 {'key':'order_id (ranged)','cardinality':'Very high','write_distribution':'Good with dispersed IDs; monotonic IDs can hotspot','query_targeting':'Good for order ID; customer lookups scatter','range_queries':'Good by order ID','assessment':'Not best for customer-centric workload'},
 {'key':'customer_id (ranged)','cardinality':'High','write_distribution':'Skew possible for high-volume customers','query_targeting':'Targets customer equality and customer ranges','range_queries':'Good for customer ID ranges','assessment':'Good if customer ranges are important'},
 {'key':'order_date (ranged)','cardinality':'High','write_distribution':'Poor for monotonically increasing inserts; hotspot risk','query_targeting':'Good for time-window queries','range_queries':'Good by date','assessment':'Avoid for high-rate chronological writes'},
 {'key':'customer_id (hashed)','cardinality':'High','write_distribution':'Generally balanced hash ranges; large single customers can still be hot','query_targeting':'Targets exact customer_id equality; not efficient for customer ID ranges','range_queries':'Scatter for range on original customer_id','assessment':'Recommended for customer-equality lookups and balanced writes'}]
result={'activity':'Lab 11.1','workload_assumption':'Many customers, frequent equality lookups by customer_id, high write volume','decision_matrix':rows,'recommendation':'customer_id (hashed)','reason':'Balances write distribution while retaining targeted equality queries on customer_id. Range queries on customer_id fan out.'}
for x in rows:print(x['key'], '|',x['write_distribution'],'|',x['query_targeting'])
print('Recommendation:',result['recommendation'])
save('lab_11_1.json',result)
