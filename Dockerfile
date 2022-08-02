FROM --platform=linux/amd64 python:3.10.5
WORKDIR /usr/src/winterdrp
#COPY ./* $HOME
#RUN  apt-get update \
#  && apt-get install -y \
#     sextractor \
#     scamp \
#     swarp \
#     wget \
#     sudo \
#     lsb-release \
#     software-properties-common \
#  && rm -rf /var/lib/apt/lists/*

## Installing confluent kakfa is such an unbelievable pain...
#RUN wget -qO - https://packages.confluent.io/deb/7.2/archive.key | sudo apt-key add -
#RUN sudo add-apt-repository "deb [arch=aarch64] https://packages.confluent.io/deb/7.2 stable main"
#RUN sudo add-apt-repository "deb https://packages.confluent.io/clients/deb $(lsb_release -cs) main"
#RUN sudo apt-get update && sudo apt-get install confluent-platform
#RUN apt install librdkafka-dev

RUN  apt-get update \
  && apt-get install -y \
     sextractor \
     scamp \
     swarp \
  && rm -rf /var/lib/apt/lists/*

COPY . .

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -e .
RUN ln -s /usr/bin/SWarp /usr/bin/swarp
RUN ln -s /usr/bin/source-extractor /usr/bin/sex
