"""Preflight validation; does not require MongoDB server."""
from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parent
scripts = sorted(ROOT.glob('0*/*.py'))
assert len(scripts) == 4, f"Expected 4 activity Python scripts, found {len(scripts)}"
for script in scripts:
    source = script.read_text(encoding='utf-8')
    ast.parse(source, filename=str(script))
    assert 'exclusiveMinimum' not in source, f"Old invalid validator in {script}"
    assert '"minimum": 0.01' in source, f"Missing fixed price validation in {script}"
    products = json.loads(script.with_name('products.json').read_text(encoding='utf-8'))
    assert len(products) >= 10
    assert all(x['price'] >= .01 and x['stock'] >= 0 for x in products)
    print('PASS:', script.relative_to(ROOT))
print('All four scripts and JSON fixtures passed static checks.')
