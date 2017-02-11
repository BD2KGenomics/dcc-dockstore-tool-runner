# dcc-dockstore-tool-runner

A Dockstore tool designed to perform file downloads from Redwood, run another Dockstore tool, and then prepare a metadata.json and upload results to Redwood.

## Running Locally

Normally you would not run directly, you are always going to run this via Dockstore or, maybe, via Docker.  For development purposes, though, you may want to setup a local environment for debugging and extending this tool.

## Install Deps

### Ubuntu 14.04

You need to make sure you have system level dependencies installed in the appropriate way for your OS.  For Ubuntu 14.04 you do:

    sudo apt-get install python-dev libxml2-dev libxslt-dev lib32z1-dev

### Python and Packages

Use python 2.7.x.

See [here](https://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/) for information on setting
up a virtual environment for Python.

If you haven't already installed pip and virtualenv, depending on your system you may
(or may not) need to use `sudo` for these:

    sudo easy_install pip
    sudo pip install virtualenv

Now to setup:

    virtualenv env
    source env/bin/activate
    pip install jsonschema jsonmerge openpyxl sets json-spec elasticsearch semver luigi python-dateutil setuptools==28.8.0 cwl-runner cwltool==1.0.20160712154127 schema-salad==1.14.20160708181155 avro==1.8.1 typing

Alternatively, you may want to use Conda, see [here](http://conda.pydata.org/docs/_downloads/conda-pip-virtualenv-translator.html)
 [here](http://conda.pydata.org/docs/test-drive.html), and [here](http://kylepurdon.com/blog/using-continuum-analytics-conda-as-a-replacement-for-virtualenv-pyenv-and-more.html)
 for more information.

    conda create -n dockstore-tool-runner-project python=2.7.11
    source activate dockstore-tool-runner-project
    pip install jsonschema jsonmerge openpyxl sets json-spec elasticsearch semver luigi python-dateutil cwl-runner cwltool==1.0.20160316150250 schema-salad==1.7.20160316150109 avro==1.7.7 typing

### Patch CWLTools

Unfortunately, we need to patch `cwltool` so we can properly handle calling nested Docker containers through it.  Specifically, we need to pass in the Docker socket and also ensure the working directory paths are consistent between the various layers of Docker calls.  If you have installed cwltool via pip in a virtualenv or conda environment make sure you patch that one and not the system version.  Customize the below for your environment.

    patch -d /usr/local/lib/python2.7/dist-packages/cwltool/ < /usr/local/lib/python2.7/dist-packages/cwltool/job.patch

### Redwood Client

You will need a copy of the Redwood client, you can download it from [here](https://s3-us-west-2.amazonaws.com/beni-dcc-storage-dev/ucsc-storage-client.tar.gz).

### Testing Command

The command below will download samples from Redwood, run fastqc from Dockstore on two fastq files, and then upload the results back to a Redwood storage system.

    # example with real files
    python DockstoreRunner.py --redwood-path `pwd`/ucsc-storage-client --redwood-token `cat accessToken` --redwood-host storage2.ucsc-cgl.org --json-encoded ew0KCSJmYXN0cV9maWxlIjogW3sNCgkJImNsYXNzIjogIkZpbGUiLA0KCQkicGF0aCI6ICJyZWR3b29kOi8vc3RvcmFnZTIudWNzYy1jZ2wub3JnLzhlYmRiMDNhLTNjOTktNWYzMi04MTFjLTlkNzRiODgxNTFlYy8yZWFkY2M2NS00NGFmLTUyN2MtYTFhNy0yMmMzYTU1ZDczNmUvRVJSMDMwODg2XzEuZmFzdHEuZ3oiDQoJfSwgew0KCQkiY2xhc3MiOiAiRmlsZSIsDQoJCSJwYXRoIjogInJlZHdvb2Q6Ly9zdG9yYWdlMi51Y3NjLWNnbC5vcmcvOGViZGIwM2EtM2M5OS01ZjMyLTgxMWMtOWQ3NGI4ODE1MWVjLzgzNDUyM2YzLTdkZGYtNTA4Ni1hMTczLTEwODA2MGFlZWU3Ny9FUlIwMzA4ODZfMi5mYXN0cS5neiINCgl9XSwNCgkicmVwb3J0X2ZpbGVzIjogW3sNCgkJImNsYXNzIjogIkZpbGUiLA0KCQkicGF0aCI6ICIuL3RtcC9FUlIwMzA4ODZfMl9mYXN0cWMuaHRtbCINCgl9LCB7DQoJCSJjbGFzcyI6ICJGaWxlIiwNCgkJInBhdGgiOiAiLi90bXAvRVJSMDMwODg2XzFfZmFzdHFjLmh0bWwiDQoJfV0sDQoJInppcHBlZF9maWxlcyI6IFt7DQoJCSJjbGFzcyI6ICJGaWxlIiwNCgkJInBhdGgiOiAiLi90bXAvRVJSMDMwODg2XzJfZmFzdHFjLnppcCINCgl9LCB7DQoJCSJjbGFzcyI6ICJGaWxlIiwNCgkJInBhdGgiOiAiLi90bXAvRVJSMDMwODg2XzFfZmFzdHFjLnppcCINCgl9XQ0KfQ== --docker-uri quay.io/wshands/fastqc:latest --dockstore-url https://dockstore.org/containers/quay.io/wshands/fastqc --workflow-type sequence_upload_qc_report --parent-uuid aea8dccd-a1b3-50c6-b92f-a8b470743d84 --vm-instance-type m4.4xlarge --vm-region us-west-2 --vm-instance-cores 16 --vm-instance-mem-gb 64 --vm-location aws --tmpdir <path with lots of storage>

This encoded string corresponds to the contents of `sample.json`.

To encode and decode online see: https://www.base64encode.org/

## Via Docker

Build the docker image:

    # patch in /usr/local/lib/python2.7/dist-packages/cwltool
    # make a tmpdir like /datastore
    docker build -t quay.io/ucsc_cgl/dockstore-tool-runner:1.0.8 .
    # fill in your JSON from Dockstore.json template as Dockstore.my.json
    mkdir /datastore; chown ubuntu:ubuntu /datastore/
    # local execution
    TMPDIR=/datastore dockstore tool launch --entry Dockstore.cwl --local-entry --json Dockstore.my.json
    # as root in /datastore
    TMPDIR=/datastore dockstore tool launch --entry ~ubuntu/gitroot/BD2KGenomics/dcc-dockstore-tool-runner/Dockstore.cwl --local-entry --json ~ubuntu/gitroot/BD2KGenomics/dcc-dockstore-tool-runner/Dockstore.my.json
    # execute published on dockstore
    dockstore tool launch --entry quay.io/ucsc_cgl/dockstore-tool-runner:1.0.8 --json Dockstore.my.json

    # running you see it launch
    cwltool --enable-dev --non-strict --enable-net --outdir /datastore/./datastore/launcher-ff6b55b3-52e8-430c-9a70-1ff295332698/outputs/ --tmpdir-prefix /datastore/./datastore/launcher-ff6b55b3-52e8-430c-9a70-1ff295332698/working/ /home/ubuntu/gitroot/BD2KGenomics/dcc-dockstore-tool-runner/Dockstore.cwl /datastore/./datastore/launcher-ff6b55b3-52e8-430c-9a70-1ff295332698/workflow_params.json

## Via cwltool
NOTE: THE ENVIRONMENT VARIABLE TMPDIR MUST BE SET TO A DIRECTORY WITH ENOUGH SPACE TO HOLD INPUT, OUTPUT AND INTERMEDIATE FILES. Otherwise cwltool will use /VAR/SPOOL/CWL by default which may not have enough space.

    cwltool --debug --enable-dev --non-strict --enable-net  <path to>/Dockstore.cwl --redwood-path `pwd`/ucsc-storage-client --redwood-token `cat accessToken` --redwood-host storage2.ucsc-cgl.org --json-encoded  ew0KCSJmYXN0cV9maWxlIjogWw0KDQoJCXsNCgkJCSJjbGFzcyI6ICJGaWxlIiwNCgkJCSJwYXRoIjogInJlZHdvb2Q6Ly9zdG9yYWdlMi51Y3NjLWNnbC5vcmcvOGViZGIwM2EtM2M5OS01ZjMyLTgxMWMtOWQ3NGI4ODE1MWVjLzJlYWRjYzY1LTQ0YWYtNTI3Yy1hMWE3LTIyYzNhNTVkNzM2ZS9FUlIwMzA4ODZfMS5mYXN0cS5neiINCgkJfSwgew0KCQkJImNsYXNzIjogIkZpbGUiLA0KCQkJInBhdGgiOiAicmVkd29vZDovL3N0b3JhZ2UyLnVjc2MtY2dsLm9yZy84ZWJkYjAzYS0zYzk5LTVmMzItODExYy05ZDc0Yjg4MTUxZWMvODM0NTIzZjMtN2RkZi01MDg2LWExNzMtMTA4MDYwYWVlZTc3L0VSUjAzMDg4Nl8yLmZhc3RxLmd6Ig0KCQl9DQoJXQ0KfQ== --dockstore-uri quay.io/wshands/fastqc --parent-uuid id --tmpdir <path with lots of storage>

## Via Dockstore
NOTE: THE ENVIRONMENT VARIABLE TMPDIR MUST BE SET TO A DIRECTORY WITH ENOUGH SPACE TO HOLD INPUT, OUTPUT AND INTERMEDIATE FILES. Otherwise cwltool (called by dockstore) will use /VAR/SPOOL/CWL by default which may not have enough space.

Sample:

    dockstore tool launch --entry quay.io/ucsc-cgl/dockstore-tool-runner:1.0.8 --json Docstore.json
    # Locally
    dockstore tool launch --entry Dockstore.cwl --local-entry --json Dockstore.json

## Known Issues

    AttributeError: 'str' object has no attribute 'append'

Looks like a bug in Python 2.7 shipped with MacOS since it was fixed on [Ubuntu](https://bugs.launchpad.net/ubuntu/+source/python2.7/+bug/1048710).

The params section of metadata.json needs to be fixed:

    "workflow_params" : {
      "%s": "%s","%s": "%s","%s": "%s","%s": "%s","%s": "%s","%s": "%s"
    }

## TODO

* need to fix the params issue
