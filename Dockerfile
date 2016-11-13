FROM ubuntu:16.04

MAINTAINER Brian O'Connor <briandoconnor@gmail.com>

WORKDIR ./

USER root

COPY DockstoreRunner.py /usr/local/bin
RUN chmod a+x /usr/local/bin/DockstoreRunner.py

# Install OpenJDK JRE, curl, python, python pip, and the docker client
RUN apt-get update && apt-get install --yes \
    openjdk-8-jre \
    curl \
    python \
    python-pip \
    docker.io \
    python-dev \
    libxml2-dev \
    libxslt-dev \
    lib32z1-dev \
    python-setuptools \
    build-essential

RUN pip install --upgrade pip
RUN pip install jsonschema jsonmerge openpyxl sets json-spec elasticsearch semver luigi

#install cwltool in the container
RUN pip install setuptools==24.0.3
RUN pip install cwl-runner cwltool==1.0.20160712154127 schema-salad==1.14.20160708181155 avro==1.8.1

# install the Redwood client code
RUN wget https://s3-us-west-2.amazonaws.com/beni-dcc-storage-dev/ucsc-storage-client.tar.gz
RUN mv ucsc-storage-client.tar.gz /usr/local/ && cd /usr/local && tar zxf ucsc-storage-client.tar.gz && rm ucsc-storage-client.tar.gz && chmod -R a+r ucsc-storage-client

# switch back to the ubuntu user so this tool (and the files written) are not owned by root
RUN groupadd -r -g 1000 ubuntu && useradd -r -g ubuntu -u 1000 ubuntu

USER ubuntu
