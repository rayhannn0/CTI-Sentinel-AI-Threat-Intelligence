"""Create DEMO accounts. Never run with production passwords."""
from app.main import db, password_hash, setup_indexes
setup_indexes()
for tenant in ('tenant1', 'tenant2'):
    for username, role in [('admin', 'admin'), ('alice', 'user'), ('bob', 'user')]:
        db.users.update_one({'tenant_id': tenant, 'username': username},
            {'$set': {'role': role, 'password_hash': password_hash('DemoPass123!')}}, upsert=True)
        print(f'{tenant}/{username} ({role}) seeded')
print('Demo password for all users: DemoPass123!')
