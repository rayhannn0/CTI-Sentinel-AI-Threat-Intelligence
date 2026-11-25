"""Run safe core activities; large benchmark and continuous monitor are opt-in."""
from seed_db import seed
from lab_7_1.lab_7_1 import run as lab_7_1
from activity_7_1.activity_7_1 import run as activity_7_1

def main():
    seed()
    lab_7_1()
    activity_7_1()
    print('Finished core setup in MongoDB Compass database: lab7')
    print('Benchmark: python3 lab_7_2/lab_7_2.py')
    print('Monitor: python3 activity_7_2/activity_7_2.py --cycles 3')
    print('Website: python3 -m backend.app')

if __name__=='__main__':
    main()
