#!/usr/bin/env cwl-runner

class: CommandLineTool
id: "dockstore-tool-runner"
label: "A Dockstore tool that can call download from Redwood, call another Dockstore tool, and then upload back to Redwood."
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

dct:creator:
  '@id': http://orcid.org/0000-0002-7681-6415
  foaf:name: Brian O'Connor
  foaf:mbox: mailto:briandoconnor@gmail.com

requirements:
  - class: DockerRequirement
    dockerPull: "quay.io/ucsc_cgl/dockstore-tool-runner:1.0.0"
hints:
  - class: ResourceRequirement
    coresMin: 1
    ramMin: 4092
    outdirMin: 512000
    description: "the process requires at least 4G of RAM"

inputs:
  redwood_token:
    type: string
    doc: "Token for storage client"
    inputBinding:
      prefix: --redwood-token

  redwood_host:
    type: string
    doc: "Host for storage client"
    inputBinding:
      prefix: --redwood-host

  json_encoded:
    type: string
    doc: "Encoded JSON for container to be run by Dockstore"
    inputBinding:
      prefix: --json-encoded

  docker_uri:
    type: string
    doc: "Path to docker image from which to create container"
    inputBinding:
      prefix: --docker-uri

  dockstore_url:
    type: string
    doc: "Path to docker image from which to create container"
    inputBinding:
      prefix: --dockstore-url

  workflow_type:
    type: string
    doc: "String that describes the workflow type: [qc, sequence_upload, sequence_upload_qc_report, alignment, alignment_qc_report, rna_seq_quantification, germline_variant_calling, somatic_variant_calling, immuno_target_pipelines]"
    inputBinding:
      prefix: --workflow-type

  parent_uuids:
    type: string
    doc: "UUIDs for parent"
    inputBinding:
      prefix: --parent-uuids

  tmpdir:
    type: string
    doc: "Path to the temporary directory where intermediate files are written"
    inputBinding:
      prefix: --tmpdir

  vm_instance_type:
    type: string
    doc: "Instance type used."
    inputBinding:
      prefix: --vm-instance-type

  vm_region:
    type: string
    doc: "Instance region."
    inputBinding:
      prefix: --vm-region

  vm_location:
    type: string
    doc: "The cloud this VM is running in e.g. 'aws'."
    inputBinding:
      prefix: --vm-location

  vm_instance_cores:
    type: int
    doc: "Instance cores."
    inputBinding:
      prefix: --vm-instance-cores

  vm_instance_mem_gb:
    type: int
    doc: "Instance memory in GB as int."
    inputBinding:
      prefix: --vm-instance-mem-gb

outputs:
  output_metadata_json:
    type: File
    outputBinding:
       glob: metadata.json
    doc: "Result metadata.json files from tool run on the host"

baseCommand: ["python", "/usr/local/bin/DockstoreRunner.py"]
