from app.rag import chunks,local_embed,normalize,history
import numpy as np

def test_chunk_size():
    v=chunks(' '.join(map(str,range(240))),100,20)
    assert len(v)==3 and len(v[0].split())==100

def test_chunk_overlap():
    v=chunks(' '.join(map(str,range(120))),100,20)
    assert v[0].split()[-20:]==v[1].split()[:20]

def test_invalid_overlap():
    import pytest
    with pytest.raises(ValueError):chunks('test',10,10)

def test_embedding_dimensions():assert local_embed(['sample']).shape==(1,384)

def test_normalized():assert np.isclose(np.linalg.norm(normalize(np.array([3.,4.]))),1)

def test_similarity():
    x=normalize(local_embed(['phishing credential link','phishing credential link']))
    assert (x[0]@x[1])>0.99
