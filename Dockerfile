FROM python:3.9-alpine3.13

WORKDIR /opt/app

ENV FLASK_APP="idrac-exporter.py"

COPY requirements.txt ./
RUN pip install --disable-pip-version-check --no-cache-dir -r requirements.txt

COPY idrac-exporter.py .
 
CMD [ "/usr/bin/env", "python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080" ]