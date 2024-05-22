FROM ubuntu:24.04

# Setup environment
ENV DEBIAN_FRONTEND noninteractive


RUN apt-get update
RUN apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        libpython3.12 \
        iverilog


COPY requirements.txt requirements.txt

RUN pip3 install -r ./requirements.txt --break-system-packages