from monitoring_dashboard import main as monitoring_main
from backup_restore import main as backup_main
if __name__=="__main__":
    print("=== LAB 14.1: MONITORING DASHBOARD ==="); monitoring_main(["--once"])
    print("=== LAB 14.2: BACKUP/RESTORE VERIFICATION ==="); backup_main()
    print("ALL LAB 14 ACTIVITIES COMPLETED.")
