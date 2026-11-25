# Lab 12 - MongoDB security and TLS assessment

Standalone Docker project; localhost port **27617**; database **lab12**.

## First run on macOS

1. Unzip into `~/Downloads/lab12/Lab12_MongoDB_Docker`
2. Start Docker Desktop.
3. Open Mac Terminal:

```bash
cd ~/Downloads/lab12/Lab12_MongoDB_Docker
python3 bootstrap.py
docker compose --profile runner build labrunner
docker compose --profile runner run --rm labrunner
python3 -m pip install -r requirements.txt
python3 generate_report.py
```

Bootstrap generates **random credentials** in `.env` and **private TLS material** in `certs/`; never publish either. Only public test samples are used.

## Compass (TLS and auth required)

Connection: `mongodb://127.0.0.1:27617/?directConnection=true&tls=true&authSource=admin`

Compass TLS settings: enable TLS; CA file = `<project>/certs/ca.crt`. Enter username `lab12_admin` and password from `.env` (`ROOT_PASSWORD`). A client certificate is optional for this setup, but the Python TLS test presents `certs/client.pem`.

## Check result files

`python3 verify_project.py` (after running). `output/*.json` contains recorded results.

## Docker Hub submission

```bash
docker login
docker tag lab12-mongodb-assessment:latest rayhann094/lab12-mongodb-assessment:latest
docker push rayhann094/lab12-mongodb-assessment:latest
printf '%s\n' 'https://hub.docker.com/r/rayhann094/lab12-mongodb-assessment' > docker_hub_url.txt
python3 make_submission_pdf.py
open Lab12_DockerHub_Submission.pdf
```

**Important:** Docker Hub image is the **assessment runner**. A demonstration needs this Compose project and `bootstrap.py`. The image itself does **not** contain credentials, certificates, or a running database. Avoid `docker compose down -v` if you want to keep stored data. For a clean reset, preserve `.env` and certificates with matching database volume or intentionally reset all three together.

## Certification and security scope

This is a teaching demo, not a production hardening guide. CA is self-signed, certificate lifetime is one year, server local TLS is required, and client certificates are allowed without mandatory mutual-TLS. User authentication is password-based; client keypair is used to demonstrate an optional client TLS identity. MongoDB internal localhost bootstrap exception is used only to create the initial root user.

## Official references

- https://www.mongodb.com/docs/manual/tutorial/configure-ssl/
- https://www.mongodb.com/docs/manual/core/collection-level-access-control/
- https://www.mongodb.com/docs/manual/reference/privilege-actions/
