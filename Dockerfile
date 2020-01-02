FROM ubuntu:bionic

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

RUN apt update && apt dist-upgrade -y && apt install -y qemu-system qemu-utils python3 python3-pip && \
    pip3 install prettytable

COPY . /opt/MacOS/.

ENTRYPOINT ["/opt/MacOS/run.py"]
