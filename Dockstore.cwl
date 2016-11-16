#!/usr/bin/env cwl-runner

class: CommandLineTool
id: "fastqc"
label: "A quality control application for high throughput sequence data"
cwlVersion: v1.0 
doc: |
    ![build_status](https://quay.io/wshands/fastqc/status)
    A Docker container for the fastqc command. 
    See the fastqc (http://www.bioinformatics.babraham.ac.uk/projects/fastqc/) 
    website for more information.
    ```
    Usage:
    # fetch CWL
    $> dockstore tool cwl --entry quay.io/wshands/fastqc > fastqc.cwl
    # make a runtime JSON template and edit it
    $> dockstore tool convert cwl2json --cwl fastqc.cwl > fastqc.json
    # run it locally with the Dockstore CLI
    $> dockstore tool launch --entry quay.io/wshands/fastqc  --json fastqc.json
    ```

#dct:creator:
#  "@id": "jshands@ucsc.edu"
#  foaf:name: Walt Shands
#  foaf:mbox: "jshands@ucsc.edu"

requirements:
  - class: DockerRequirement
    dockerPull: "quay.io/wshands/fastqc"

hints:
  - class: ResourceRequirement
    coresMin: 1
    ramMin: 4092
    outdirMin: 512000
    description: "the process requires at least 4G of RAM"

inputs:
  fastq_file:
#    type: File # No reason to accept multiple files as no overall report is generated
#    inputBinding:
#      position: 1
    type:
      type: array
      items: File
    inputBinding:
      position: 1
  bar:
    type: string
    inputBinding:
      position: 2
  foo:
    type: int  
    inputBinding:
      position: 3

#baseCommand: [ fastqc, "--outdir", . , "--extract"]
baseCommand: [ fastqc, "--outdir", .]

#outputs:
#  zippedFile:
#    type: File
#    outputBinding:
#      glob: "*.zip"
#  report:
#    type: File
#    outputBinding:
#      glob: "./*"

outputs:
  zipped_files:
    type:
      type: array
      items: File
    outputBinding:
      # should be put in the working directory
       glob: "*.zip"
    doc: "Individual graph files and additional data files
containing the raw data from which plots were drawn."

  report_files:
    type:
      type: array
      items: File
    outputBinding:
      # should be put in the working directory
       glob: "*.html"
    doc: "HTML reports with embedded graphs"


