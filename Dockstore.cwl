#!/usr/bin/env cwl-runner

class: CommandLineTool
id: "dockstore_tool_runner"
label: "container that can call dockstore"
cwlVersion: v1.0
doc: |
    ![build_status](https://quay.io/wshands/dockstore_tool_runner/status)
    A Docker container from which Dockstore containers may be launched.
    ```
    Usage:
    # fetch CWL
    $> dockstore tool cwl --entry quay.io/wshands/dockstore_tool_runner > dockstore_tool_runner.cwl
    # make a runtime JSON template and edit it
    $> dockstore tool convert cwl2json --cwl dockstore_tool_runner.cwl > dockstore_tool_runner.json
    # run it locally with the Dockstore CLI
    $> dockstore tool launch --entry quay.io/wshands/dockstore_tool_runner  --json dockstore_tool_runner.json
    ```

#dct:creator:
#  "@id": "jshands@ucsc.edu"
#  foaf:name: Walt Shands
#  foaf:mbox: "jshands@ucsc.edu"

requirements:
  - class: DockerRequirement
    dockerPull: "quay.io/wshands/dockstore_tool_runner"
#    dockerImageId: dockstore_tool_runner
  #need this since dockstore is in 
  #/home/ubuntu and the HOME dir is set by 
  #cwltool as /var/... 
#  - class: EnvVarRequirement
#    envDef:
#      - envName: HOME
#        envValue: "/home/ubuntu"
#        envValue: $(inputs.HOME)

#arguments:
#  - valueFrom: tool
#  - valueFrom: launch

hints:
  - class: ResourceRequirement
    coresMin: 1
    ramMin: 4092
    outdirMin: 512000
    description: "the process requires at least 4G of RAM"

inputs:
  json_file:
    type: File
    doc: "Path to JSON file for container to be run by Dockstore"
    inputBinding:
      prefix: --json_file

  docker_image:
    type: string
    doc: "Path to docker image from which to create container"
    inputBinding:
      prefix: --docker_image

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


baseCommand: ["dockstore_tool_runner.py"]
