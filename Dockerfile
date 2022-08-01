FROM python:3.10.5-alpine3.16
WORKDIR /usr/src/winterdrp
#COPY ./* $HOME
RUN  apt-get update \
  && apt-get install -y \
     sextractor \
     scamp \
     swarp \
  && rm -rf /var/lib/apt/lists/*

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY . .
RUN pip install -e .
RUN alias swarp=SWarp
RUN alias sex=/usr/bin/source-extractor
