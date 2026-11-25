"""Restore the original three data-bearing voting members safely.

MongoDB permits changing AT MOST ONE voting member per normal reconfig.
We first remove the arbiter, then restore each non-voting data member's vote.
No force, database drop, Docker volume deletion, or reset is performed.
"""
import time
from connection import member_client, wait_for_primary, status_summary
from docker_utils import compose


def read_config():
    client = member_client(wait_for_primary())
    try:
        return client.admin.command('replSetGetConfig')['config']
    finally:
        client.close()


def reconfigure(cfg, description):
    cfg['version'] += 1
    client = member_client(wait_for_primary())
    try:
        print(description, flush=True)
        client.admin.command({'replSetReconfig': cfg})
    finally:
        client.close()
    # Election / reconfiguration can briefly interrupt primary availability.
    wait_for_primary(timeout=90)
    time.sleep(2)


def main():
    cfg = read_config()
    arbiters = [m for m in cfg['members'] if m.get('arbiterOnly')]
    if arbiters:
        # Removing ONE arbiter voter in its own operation avoids MongoDB error 103.
        for arbiter in arbiters:
            cfg = read_config()
            cfg['members'] = [m for m in cfg['members'] if m['_id'] != arbiter['_id']]
            reconfigure(cfg, f"Removing arbiter {arbiter['host']} (one voting change)...")
    else:
        print('No arbiter in replica set configuration.')

    # Restore each data-bearing voting member separately (if needed).
    cfg = read_config()
    for member in cfg['members']:
        if member.get('votes', 1) == 0:
            host = member['host']
            cfg = read_config()
            target = next(m for m in cfg['members'] if m['host'] == host)
            target['votes'] = 1
            target['priority'] = 1
            reconfigure(cfg, f'Restoring vote for {host} (one voting change)...')

    # Priority-only adjustment: no voting membership changes in this operation.
    cfg = read_config()
    changed = False
    for member in cfg['members']:
        name = member['host'].split(':')[0]
        target_priority = 2 if name == 'mongo1' else 1
        if member.get('priority', 1) != target_priority:
            member['priority'] = target_priority
            changed = True
    if changed:
        reconfigure(cfg, 'Restoring baseline priorities (mongo1=2; other data nodes=1)...')

    # Stop arbiter container only after removing it from the replica set.
    if arbiters:
        compose('--profile', 'arbiter', 'stop', 'arbiter', check=False)
    cfg = read_config()
    members = cfg['members']
    if len(members) != 3 or any(m.get('arbiterOnly') or m.get('votes', 1) != 1 for m in members):
        raise RuntimeError('Baseline check failed; inspect replica set configuration before proceeding.')
    print('BASELINE RESTORED: 3 data-bearing voting members; no arbiter.')
    status_summary()


if __name__ == '__main__':
    main()
