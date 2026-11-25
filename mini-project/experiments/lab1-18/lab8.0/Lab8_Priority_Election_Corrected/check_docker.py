"""Run this before bootstrapping the Lab 8 replica set."""
from docker_utils import check_docker

if __name__ == '__main__':
    try:
        executable = check_docker()
    except RuntimeError as exc:
        print('DOCKER SETUP REQUIRED:', exc)
        raise SystemExit(1)
    print('PASS: Docker Engine and Compose are available.')
    print('Docker CLI:', executable)
