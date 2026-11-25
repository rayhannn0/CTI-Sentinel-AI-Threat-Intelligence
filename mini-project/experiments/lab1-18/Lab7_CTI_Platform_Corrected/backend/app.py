"""Flask UI and read-only CTI demonstration API."""
import os
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from pymongo.errors import PyMongoError
from connection import get_db

ROOT = Path(__file__).resolve().parent.parent
app = Flask(__name__, static_folder=str(ROOT / 'frontend'), static_url_path='')

def clean(doc):
    item = dict(doc)
    item['_id'] = str(item['_id'])
    return item

def bounded_int(name, default, minimum, maximum):
    raw = request.args.get(name, str(default))
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return None
    return value if minimum <= value <= maximum else None

@app.get('/')
def home():
    return send_from_directory(str(ROOT / 'frontend'), 'index.html')

@app.get('/api/health')
def health():
    try:
        db = get_db()
        db.command('ping')
        return jsonify(status='ok', database=db.name, warning='Synthetic demo threats, not verified intelligence')
    except PyMongoError as exc:
        return jsonify(status='error', message=str(exc)), 503

@app.get('/api/threats')
def threats():
    page = bounded_int('page', 1, 1, 1000000)
    limit = bounded_int('limit', 30, 1, 100)
    if page is None or limit is None:
        return jsonify(error='page must be >=1 and limit must be 1..100'), 400
    filters = {}
    query = request.args.get('q', '').strip()
    if len(query) > 200:
        return jsonify(error='Search must be at most 200 characters'), 400
    if query:
        filters['$text'] = {'$search': query}
    for name in ('platform','status','severity'):
        v = request.args.get(name,'').strip()
        if v:
            filters[name] = v
    db = get_db()
    count = db.threats.count_documents(filters)
    docs = list(db.threats.find(filters).sort('_id', 1).skip((page-1)*limit).limit(limit))
    return jsonify(items=[clean(d) for d in docs], count=count, page=page,
                   data_warning='Synthetic educational records; do not treat as verified intelligence')

@app.get('/api/threats/<threat_id>')
def threat_detail(threat_id):
    doc = get_db().threats.find_one({'_id':threat_id})
    if doc is None:
        return jsonify(error='Threat not found'),404
    return jsonify(clean(doc))

@app.get('/api/stats')
def stats():
    db = get_db()
    def counts(field):
        return {str(x['_id']): x['count'] for x in db.threats.aggregate([
            {'$group': {'_id':f'${field}', 'count':{'$sum':1}}}
        ])}
    return jsonify(total=db.threats.count_documents({}), by_status=counts('status'),
                   by_severity=counts('severity'))

@app.get('/api/reports')
def reports():
    return jsonify([clean(d) for d in get_db().reports.find().sort('_id',-1).limit(100)])

@app.errorhandler(PyMongoError)
def mongo_error(exc):
    app.logger.exception('MongoDB operation failed')
    return jsonify(error='MongoDB operation failed', detail=str(exc)), 503

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
