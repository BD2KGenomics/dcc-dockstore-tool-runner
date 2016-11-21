#!/usr/bin/env cwl-runner

class: CommandLineTool
id: "dockstore_tool_runner"
label: "container that can call dockstore"
cwlVersion: v1.0
doc: |
    ![build_status](https://quay.io/ucsc_cgl/DockstoreRunner/status)
    A Docker container from which Dockstore containers may be launched.
    ```
    Usage:
    # fetch CWL
    $> dockstore tool cwl --entry quay.io/ucsc_cgl/DockstoreRunner > Dockstore.cwl
    # make a runtime JSON template and edit it
    $> dockstore tool convert cwl2json --cwl Dockstore.cwl > Dockstore.json
    # run it locally with the Dockstore CLI
    $> dockstore tool launch --entry quay.io/ucsc_cgl/DockstoreRunner  --json Dockstore.json
    ```

#dct:creator:
#  "@id": "jshands@ucsc.edu"
#  foaf:name: Walt Shands
#  foaf:mbox: "jshands@ucsc.edu"

requirements:
  - class: DockerRequirement
    dockerPull: "quay.io/ucsc_cgl/DockstoreRunner"
hints:
  - class: ResourceRequirement
    coresMin: 1
    ramMin: 4092
    outdirMin: 512000
    description: "the process requires at least 4G of RAM"

inputs:
  redwood-path:
    type: string
    doc: "Path to storage client"
    inputBinding:
      prefix: --redwood-path

  redwood-token:
    type: string
    doc: "Token for storage client"
    inputBinding:
      prefix: --redwood-token

  redwood-host:
    type: string
    doc: "Host for storage client"
    inputBinding:
      prefix: --redwood-host
 
  json-encoded:
    type: string
    doc: "Encoded JSON for container to be run by Dockstore"
    inputBinding:
      prefix: --json-encoded

  dockstore-uri:
    type: string
    doc: "Path to docker image from which to create container"
    inputBinding:
      prefix: --dockstore-uri

  parent-uuid:
    type: string
    doc: "UUID for parent"
    inputBinding:
      prefix: --parent-uuid

  tmpdir:
    type: string
    doc: "Path to the temporary directory where intermediate files are written"
    inputBinding:
      prefix: --tmpdir

outputs:
  output_files:
    type:
      type: array
      items: File
    outputBinding:
      # should be put in the working directory
       glob: ./*
    doc: "Result files from container run on the host"


baseCommand: ["DockstoreRunner.py"]
