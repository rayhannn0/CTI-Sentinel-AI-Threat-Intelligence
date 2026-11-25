"""Activity 7.1: create embedded source snapshots with an aggregation join."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from connection import get_db

def run():
    db=get_db()
    # Replaces only this lab's derived collection, never modifies original threats/sources.
    pipeline=[
        {'$lookup':{'from':'sources','localField':'source_ids',
                    'foreignField':'_id','as':'sources_embedded'}},
        {'$addFields':{'source_evaluation':{
            '$cond':[{'$gt':[{'$size':'$sources_embedded'},0]},
                     'source_linked_unverified','source_missing_unverified']}}},
        {'$merge':{'into':'threats_embedded','on':'_id',
                   'whenMatched':'replace','whenNotMatched':'insert'}}
    ]
    list(db.threats.aggregate(pipeline))
    print('Embedded records:',db.threats_embedded.count_documents({}))
    for doc in db.threats_embedded.find({}, {'_id':1,'sources_embedded.name':1,'source_evaluation':1}).limit(3):
        print(doc)
    print('Faster: one threat query loads source snapshots without $lookup.')
    print('Harder: keeping copied source names/metadata synchronized.')
    print('A linked source does NOT prove a threat is real. Evidence verification is separate.')

if __name__=='__main__':
    run()
