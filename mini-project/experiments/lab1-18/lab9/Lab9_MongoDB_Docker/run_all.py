"""Host launcher. Network partition is separate, intentional and safely reversible."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
cmds=[['python3','bootstrap.py'],['docker','compose','--profile','runner','run','--rm','labrunner','python','run_benchmarks.py']]
for cmd in cmds:
 print('RUN:',' '.join(cmd),flush=True)
 result=subprocess.run(cmd,cwd=root)
 if result.returncode:sys.exit(result.returncode)
print('Benchmarks done. For the partition lab, run: python3 partition_controller.py')
