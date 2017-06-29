FROM python:2

COPY . /opt/osc
RUN pip install --no-cache-dir -r /opt/osc/requirements.txt
WORKDIR /opt/osc/cache
ENTRYPOINT [ "/usr/local/bin/python" , "/opt/osc/upload_video.py", "-p", "/data" ]

