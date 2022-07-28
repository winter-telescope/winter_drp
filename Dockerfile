FROM debian
WORKDIR /usr/src/winterdrp
#COPY ./* $HOME
RUN  apt-get update \
  && apt-get install -y \
     sextractor \
     scamp \
     swarp \
  && rm -rf /var/lib/apt/lists/*

FROM python:3.10
RUN /usr/local/bin/python -m pip install --upgrade pip
COPY . .

RUN pip install -e .
