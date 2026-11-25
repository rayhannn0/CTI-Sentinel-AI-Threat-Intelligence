from app.main import password_hash, verify_password, scoped_query

def test_password():
    encoded = password_hash('securepassword')
    assert verify_password('securepassword', encoded)
    assert not verify_password('wrong', encoded)

def test_admin_scope():
    assert scoped_query({'tenant_id': 'acme', 'id': '123', 'role': 'admin'}) == {'tenant_id': 'acme'}

def test_user_scope():
    assert scoped_query({'tenant_id': 'acme', 'id': '123', 'role': 'user'}) == {'tenant_id': 'acme', 'owner_id': '123'}
