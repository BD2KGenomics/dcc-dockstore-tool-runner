FROM quay.io/ucsc_cgl/redwood-client:1.1.1

MAINTAINER Walt Shands jshands@ucsc.edu

#patch logback.xml so the storage client writes its log files to /tmp because other
#directories are readonly when cwltool runs the container
RUN sed -i 's~<property name=\"log.dir\" value=\"${logging.path:-/tmp/icgc-storage-client/logs}\" />~<property name=\"log.dir\" value=\"/tmp/icgc-storage-client/logs\" />~g' /dcc/icgc-storage-client/conf/logback.xml

RUN sed -i 's~<property name=\"log.dir\" value=\"${LOG_PATH:-../logs}\" />~<property name=\"log.dir\" value=\"/tmp/dcc-metadata-client/logs\" />~g' /dcc/dcc-metadata-client/conf/logback.xml


WORKDIR ./

USER root

# Install OpenJDK JRE, curl, python, python pip, and the docker client
RUN apt-get update && apt-get install --yes \
    curl \
    wget \
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
RUN pip install jsonschema jsonmerge openpyxl sets json-spec elasticsearch semver

#install cwltool in the container
#use the version required by dockstore
RUN pip install setuptools==28.8.0
RUN pip install cwl-runner cwltool==1.0.20170217172322 schema-salad==2.2.20170222151604 avro==1.8.1
RUN pip install functools32==3.2.3.post2

#Patch the cwltool code that sets up the docker run command line
#so that it includes '-v /var/run/docker.sock:/var/run/docker.sock
#and the mount point for the directory specified by the host environment
#variable TMPDIR
#this will allow the docker run command generated by cwltools inside
#this container to access the host's docker engine
#and launch containers outside this container
#and which will be able to access the same TMPDIR on the host
#this patch addes code to job.py and assumes the file is at
#/usr/local/lib/python2.7/dist-packages/cwltool/job.py
#TODO?? make sure the path exists and the current version
#of python is the right one?
#COPY job.patch /usr/local/lib/python2.7/dist-packages/cwltool/job.patch
#RUN patch -d /usr/local/lib/python2.7/dist-packages/cwltool/ < /usr/local/lib/python2.7/dist-packages/cwltool/job.patch
#COPY process.patch /usr/local/lib/python2.7/dist-packages/cwltool/process.patch
#RUN patch -d /usr/local/lib/python2.7/dist-packages/cwltool/ < /usr/local/lib/python2.7/dist-packages/cwltool/process.patch

#Add ubuntu user and group
RUN groupadd -r -g 1000 ubuntu && useradd -r -g ubuntu -u 1000 ubuntu

#create /home/ubuntu in the root as owned by ubuntu
RUN mkdir /home/ubuntu
RUN chown ubuntu:ubuntu /home/ubuntu

#install Dockstore for user ubuntu
COPY .dockstore/ /home/ubuntu/.dockstore
RUN chown -R ubuntu:ubuntu /home/ubuntu/.dockstore
COPY Dockstore/ /home/ubuntu/Dockstore
RUN chown -R ubuntu:ubuntu /home/ubuntu/Dockstore && chmod a+x /home/ubuntu/Dockstore/dockstore

ENV PATH /home/ubuntu/Dockstore/:$PATH
#ENV HOME /home/ubuntu

#copy dockstore files to root so root can run dockstore
COPY .dockstore/ /root/.dockstore
COPY Dockstore/ /root/Dockstore
RUN chmod a+x /root/Dockstore/dockstore

ENV PATH /root/Dockstore/:$PATH
ENV HOME /root

COPY DockstoreRunner.py /usr/local/bin
RUN chmod a+x /usr/local/bin/DockstoreRunner.py

#since we have not figured out how to run as nonroot
#set the following env var so dockstore does not question
#the fact that we are running as root
ENV DOCKSTORE_ROOT 1

#container must run as root in order to access docker.sock on the host
#becuase ubuntu is not a member of the host's docker.sock docker group
#and there is no way to set this up at build time
USER root
