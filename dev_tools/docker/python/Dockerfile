
FROM python:3.10

WORKDIR /app

RUN apt update \
  && apt install tk \
  && pip install customtkinter Pillow\
  && apt -y autoclean \
  && apt clean

RUN mkdir /home/user \
  && useradd user --uid=1000  \
  && chown 1000:1000 /home/user

#COPY . .

#CMD [ "python3", "./test_app.py" ]
