# dcc-dockstore-tool-runner
A Dockstore tool designed to perform file downloads from Redwood, run another Dockstore tool, and then upload to Redwood.

## Running Locally

Normally you would not run locally, you are always going to run this via Dockstore or, maybe, via Docker.  For development purposes, though, you may want to setup a local environment for debugging and extending this tool.

## Install Deps

### Ubuntu 14.04

You need to make sure you have system level dependencies installed in the appropriate way for your OS.  For Ubuntu 14.04 you do:

    sudo apt-get install python-dev libxml2-dev libxslt-dev lib32z1-dev

### Python

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
    pip install jsonschema jsonmerge openpyxl sets json-spec elasticsearch semver luigi python-dateutil cwl-runner cwltool==1.0.20160316150250 schema-salad==1.7.20160316150109 avro==1.7.7 typing

Alternatively, you may want to use Conda, see [here](http://conda.pydata.org/docs/_downloads/conda-pip-virtualenv-translator.html)
 [here](http://conda.pydata.org/docs/test-drive.html), and [here](http://kylepurdon.com/blog/using-continuum-analytics-conda-as-a-replacement-for-virtualenv-pyenv-and-more.html)
 for more information.

    conda create -n schemas-project python=2.7.11
    source activate schemas-project
    pip install jsonschema jsonmerge openpyxl sets json-spec elasticsearch semver luigi python-dateutil cwl-runner cwltool==1.0.20160316150250 schema-salad==1.7.20160316150109 avro==1.7.7 typing

### Redwood Client

    https://s3-us-west-2.amazonaws.com/beni-dcc-storage-dev/ucsc-storage-client.tar.gz

### Testing Command

    python DockstoreRunner.py --redwood-path foo --redwood-token token --redwood-host host --json-encoded e30= --dockstore-uri uri --parent-uuid id

    python DockstoreRunner.py --redwood-path `pwd`/ucsc-storage-client --redwood-token `cat accessToken` --redwood-host storage2.ucsc-cgl.org --json-encoded ew0KICAgICJmYXN0cV9maWxlIjogWw0KICAgICAgICB7DQogICAgICAgICJjbGFzcyI6ICJGaWxlIiwNCiAgICAgICAgInBhdGgiOiAicmVkd29vZDovL3N0b3JhZ2UudWNzYy1jZ2wub3JnL2YzOTJmNzljLWE5ZjMtMTFlNi04MGY1LTc2MzA0ZGVjN2ViNy9mMzkzMDBmYy1hOWYzLTExZTYtODBmNS03NjMwNGRlYzdlYjcvTkExMjg3OC1OR3YzLUxBQjEzNjAtQV8xLmZhc3RxLmd6Ig0KICAgICAgICB9LA0KICAgICAgICB7DQogICAgICAgICJjbGFzcyI6ICJGaWxlIiwNCiAgICAgICAgInBhdGgiOiAicmVkd29vZDovL3N0b3JhZ2UudWNzYy1jZ2wub3JnL2YzOTJmNzljLWE5ZjMtMTFlNi04MGY1LTc2MzA0ZGVjN2ViNy9mMzkyZmVhNC1hOWYzLTExZTYtODBmNS03NjMwNGRlYzdlYjcvTkExMjg3OC1OR3YzLUxBQjEzNjAtQV8yLmZhc3RxLmd6Ig0KICAgICAgICB9DQogICAgXQ0KfQ== --dockstore-uri quay.io/wshands/fastqc --parent-uuid id

    # another encoded doc
    python DockstoreRunner.py --redwood-path `pwd`/ucsc-storage-client --redwood-token `cat accessToken` --redwood-host storage2.ucsc-cgl.org --json-encoded ew0KCSJmYXN0cV9maWxlIjogWw0KDQoJCXsNCgkJCSJjbGFzcyI6ICJGaWxlIiwNCgkJCSJwYXRoIjogInJlZHdvb2Q6Ly9zdG9yYWdlMi51Y3NjLWNnbC5vcmcvOGViZGIwM2EtM2M5OS01ZjMyLTgxMWMtOWQ3NGI4ODE1MWVjLzJlYWRjYzY1LTQ0YWYtNTI3Yy1hMWE3LTIyYzNhNTVkNzM2ZS9FUlIwMzA4ODZfMS5mYXN0cS5neiINCgkJfSwgew0KCQkJImNsYXNzIjogIkZpbGUiLA0KCQkJInBhdGgiOiAicmVkd29vZDovL3N0b3JhZ2UyLnVjc2MtY2dsLm9yZy84ZWJkYjAzYS0zYzk5LTVmMzItODExYy05ZDc0Yjg4MTUxZWMvODM0NTIzZjMtN2RkZi01MDg2LWExNzMtMTA4MDYwYWVlZTc3L0VSUjAzMDg4Nl8yLmZhc3RxLmd6Ig0KCQl9DQoJXQ0KfQ== --dockstore-uri quay.io/wshands/fastqc --parent-uuid id

This encoded string corresponds to the contents of `sample.json`.

## Via Docker

## Via Dockstore

## Known Issues

    AttributeError: 'str' object has no attribute 'append'

Looks like a bug in Python 2.7 shipped with MacOS since it was fixed on [Ubuntu](https://bugs.launchpad.net/ubuntu/+source/python2.7/+bug/1048710).
