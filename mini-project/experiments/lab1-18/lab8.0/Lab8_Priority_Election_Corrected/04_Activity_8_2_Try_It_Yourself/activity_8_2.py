"""Lab 8.2 Try It Yourself: controlled priority-election experiment.

An election is not generally guaranteed by priority alone. To make the lab's
prediction test meaningful, only the selected secondary is allowed to stand
for election (the other secondary receives priority=0 temporarily).
All original priorities are restored in a finally block.
"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pymongo.errors import PyMongoError
from connection import member_client, wait_for_primary, status_summary


def reconfigure_priorities(conf, priorities):
    for member in conf["members"]:
        name = member["host"].split(":")[0]
        if name in priorities:
            member["priority"] = priorities[name]
    conf["version"] += 1
    return conf


def restore_priorities(original):
    """Best-effort rollback, including when an election interrupts the test."""
    try:
        primary = wait_for_primary(timeout=80)
        client = member_client(primary)
        try:
            conf = client.admin.command("replSetGetConfig")["config"]
            conf = reconfigure_priorities(conf, original)
            client.admin.command({"replSetReconfig": conf})
            print("Original member priorities restored:", original)
        finally:
            client.close()
    except Exception as err:
        print("WARNING: could not restore priorities automatically:", err)
        print("Inspect rs.conf() and run restore_baseline.py before retrying.")


def main():
    primary = wait_for_primary()
    client = member_client(primary)
    try:
        conf = client.admin.command("replSetGetConfig")["config"]
        if any(m.get("arbiterOnly", False) for m in conf["members"]):
            raise RuntimeError("Restore the three-data-node baseline before priority testing: python3 restore_baseline.py")
        status = client.admin.command("replSetGetStatus")
        healthy_secondaries = {
            m["name"].split(":")[0]
            for m in status["members"]
            if m.get("stateStr") == "SECONDARY" and m.get("health") == 1
        }
        candidates = [
            m["host"].split(":")[0]
            for m in conf["members"]
            if m["host"].split(":")[0] != primary
            and m.get("votes", 1) == 1
            and m["host"].split(":")[0] in healthy_secondaries
        ]
        if len(candidates) != 2:
            raise RuntimeError("Requires two healthy, voting SECONDARY members. Check connection.py.")
        # Choose one healthy secondary; the other will be temporarily
        # non-electable to avoid a race between two eligible candidates.
        predicted = sorted(candidates)[0]
        other = next(n for n in candidates if n != predicted)
        original = {m["host"].split(":")[0]: m.get("priority", 1) for m in conf["members"]}
        print("Current primary:", primary)
        print("Predicted election winner:", predicted)
        print("Experiment: set", predicted, "priority=5;", other, "priority=0;", primary, "priority=1")
        try:
            conf = reconfigure_priorities(conf, {predicted: 5, other: 0, primary: 1})
            client.admin.command({"replSetReconfig": conf})
            print("Priority configuration applied.")
        finally:
            client.close()
    except Exception:
        client.close()
        raise

    try:
        # Reconfiguration can trigger a priority takeover on its own. This
        # is a legitimate election result; do not claim stepDown occurred.
        current = wait_for_primary(timeout=80)
        if current != primary:
            print("Priority takeover occurred before explicit stepDown:", primary, "->", current)
        else:
            step_client = member_client(primary)
            try:
                try:
                    step_client.admin.command({"replSetStepDown": 30, "secondaryCatchUpPeriodSecs": 5})
                    print("stepDown command accepted")
                except PyMongoError as err:
                    print("Connection interrupted during expected stepDown:", type(err).__name__)
            finally:
                step_client.close()

        # A temporary election or takeover can lag a few seconds. Give the
        # high-priority eligible candidate a chance to become primary.
        deadline = time.monotonic() + 45
        actual = None
        while time.monotonic() < deadline:
            try:
                actual = wait_for_primary(timeout=10)
            except RuntimeError:
                actual = None
            if actual == predicted:
                break
            time.sleep(2)
        print("Predicted primary:", predicted)
        print("Actual primary:", actual)
        print("Prediction correct:", actual == predicted)
        if actual != predicted:
            print("NOTE: election results depend on member eligibility, replication freshness and timing; review rs.status().")
        status_summary()
    finally:
        restore_priorities(original)


if __name__ == "__main__":
    main()
