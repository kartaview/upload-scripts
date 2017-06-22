FROM python:3

WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "./upload_photos_by_exif.py", "-p", "/data" ]

