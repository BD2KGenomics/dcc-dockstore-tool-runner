#!/usr/bin/env python
from __future__ import print_function, division


"""
    author Brian O'Connor
    broconno@ucsc.edu

    author Walt Shands
    jshands@ucsc.edu

    This module launches a tool and uploads metadata and result files. It first
    downloads input files from the UCSC-cgl.org storage system, then launches
    the Dockstore tool, then creates metadata describing the inputs and results,
    uploades the metadata and then uploads the result files.

"""

import json
import time
import re
from datetime import datetime
import subprocess
import argparse
import base64
import os
from urllib import urlopen
from uuid import uuid4

import logging
import hashlib
import errno
from functools import partial

import os
import sys


class DockstoreRunner:

    def __init__(self):
        self.MAX_ATTEMPTS = 3
        self.DELAY_IN_SECONDS = 30
        self.MAX_PIPELINE_ATTEMPTS= 1

        parser = argparse.ArgumentParser(description='Downloads, runs tool via Dockstore, then uploads results.')
        parser.add_argument('--program-name', default='DEV', required=True)
        parser.add_argument('--redwood-path', default='/usr/local/ucsc-storage-client', required=False)
        parser.add_argument('--redwood-token', default='token-UUID-dummy-value', required=True)
        parser.add_argument('--redwood-host', default='redwood.io', required=True)
        parser.add_argument('--redwood-auth-host', default='undefined', required=False)
        parser.add_argument('--redwood-metadata-host', default='undefined', required=False)
        parser.add_argument('--json-encoded', default='e30=', required=True)
        parser.add_argument('--docker-uri', default='quay.io/wshands/fastqc:latest', required=True)
        parser.add_argument('--dockstore-url', default='https://dockstore.org/containers/quay.io/wshands/fastqc', required=True)
        parser.add_argument('--launch-type', default='tool', const='tool', nargs='?', 
                         choices=['tool', 'workflow'], required=False, 
                         help='run a workflow or tool (default: %(default)s)')
        parser.add_argument('--workflow-type', default='sequence_upload_qc_report', required=True)
        parser.add_argument('--parent-uuids', default='parent-UUID-dummy-value', required=True)
        # FIXME: this append seems to crash on the mac but it would be the way to go if we want multiple parents
        #parser.add_argument('--parent-uuid', default='parent-UUID-dummy-value', action='append', required=True)
        parser.add_argument('-d', '--tmpdir', type=str, required=True,
                        help="Path to tmpdir, e.g. /path/to/temporary directory for"
                        " container to write intermediate files.")
        parser.add_argument('--vm-instance-type', default='unknown', required=True)
        parser.add_argument('--vm-region', default='unknown', required=True)
        parser.add_argument('--vm-instance-cores', type=int, default='unknown', required=True)
        parser.add_argument('--vm-instance-mem-gb', type=int, default='unknown', required=True)
        parser.add_argument('--vm-location', default='unknown', required=True, help='the cloud e.g. aws')
        'm4.4xlarge', 'us-west-2', 16, 64, 'aws'

        # get args
        args = parser.parse_args()
        self.program_name = args.program_name
        self.redwood_path = args.redwood_path
        self.redwood_host = args.redwood_host
        self.redwood_auth_host = args.redwood_auth_host
        if self.redwood_auth_host == 'undefined':
            self.redwood_auth_host = self.redwood_host
        self.redwood_metadata_host = args.redwood_metadata_host
        if self.redwood_metadata_host == 'undefined':
            self.redwood_metadata_host = self.redwood_host
        self.redwood_token = args.redwood_token
        self.json_encoded = args.json_encoded
        self.docker_uri = args.docker_uri
        self.dockstore_url = args.dockstore_url
        self.workflow_name = args.docker_uri.split(':')[0]
        self.workflow_version = args.docker_uri.split(':')[1]
        self.launch_type = args.launch_type
        self.workflow_type = args.workflow_type
        self.parent_uuids = args.parent_uuids
        self.bundle_uuid = uuid4()
        self.vm_instance_type = args.vm_instance_type
        self.vm_region = args.vm_region
        self.vm_instance_cores = args.vm_instance_cores
        self.vm_instance_mem_gb = args.vm_instance_mem_gb
        self.vm_location = args.vm_location
        #self.tmp_dir = './datastore-tool-launcher'
        self.tmp_dir = args.tmpdir
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        if not os.path.exists(self.tmp_dir+"/upload/"+str(self.bundle_uuid)):
            os.makedirs(self.tmp_dir+"/upload/"+str(self.bundle_uuid))
        # run
        self.run()

    def run_command(self, command_string, max_attempts, delay_in_seconds, ignore_errors=False, cwd='.'):
        print(command_string)
        #command must be formatted as a list of strings; e.g.
        #command = ["dockstore", "tool", "launch", "--debug", "--entry", self.docker_uri, "--json", "transformed_json_path"]
        command = command_string.split()
        print("command list object:")
        print(command)
        for attempt_number in range(1, max_attempts+1):
            if attempt_number > 1:
                #we are about to retry the command, but sleep for a number of seconds before retrying
                print("Waiting for "+str(delay_in_seconds)+" seconds before retrying")
                time.sleep(delay_in_seconds)

            print("\nDockstore tool runner executing command: " + command_string)
            print("Attempt number "+str(attempt_number)+" of "+str(max_attempts))
            try:
                subprocess.check_call(command, cwd=cwd)
            except subprocess.CalledProcessError as e:
                #If we get here then the called command return code was non zero
                print("\nERROR!!! DOCKSTORE TOOL RUNNER CMD:" + command_string + " FAILED !!!", file=sys.stderr)
                print("\nReturn code:" + str(e.returncode), file=sys.stderr)
                return_code = e.returncode
                if ignore_errors:
                    break;
            except Exception as e:
                print("\nERROR!!! DOCKSTORE TOOL RUNNER CMD:" + command_string + " THREW AN EXCEPTION !!!", file=sys.stderr)
                print("\nException information:" + str(e), file=sys.stderr)
                #if we get here the called command threw an exception other than just
                #returning a non zero return code, so just set the return code to 1.
                return_code = 1
                if ignore_errors:
                    break;
            #in try constructs, the else block runs if no exception happened
            #which in this case indicates the command succeeded
            else:
                print("CMD "+ command_string + " SUCCESSFUL IN DOCKSTORE TOOL RUNNER!!")
                return_code = 0
                #break out of the retry loop since the command was successful
                break;
        #the else block is executed if the loop didn't exit abnormally (i.e. with break in
        #the try: else: statement that indicates the command was successful
        else:
            if not ignore_errors:
                print("Exiting Dockstore tool runner due to call error in command "+command_string+" after "+str(max_attempts)+" attempts", file=sys.stderr)
                sys.exit(return_code)
            else:
                print ("There were errors in the call to command "+command_string+" after "+str(max_attempts)+" attempts but ignore_errors=True so ignoring ", file=sys.stderr)

    ''' output files filled into a dict '''
    def fill_in_file_dict(self, file_map, parsed_json):
        file_map['file_size'] = parsed_json['size']
        file_map['file_checksum'] = parsed_json['checksum']
        file_map['file_path'] = parsed_json['basename']
        extension = parsed_json['basename'].split('.')
        file_map['file_type'] = extension[-1]
        # FIXME: hack to deal with a few common types, this is ugly, this is a bad place to include this logic!  Better to have the indexer maintain a mapping table of types I think.
        if (parsed_json['basename'].endswith('.fastq.gz')):
            file_map['file_type'] = '.fastq.gz'

    ''' Make a dict for output files '''
    def map_outputs(self):
        # going to need to read from datastore
        # FIXME: if multiple instances of this script run at the same time it will get confused out the output dir
        result = []
        path = self.tmp_dir+"/datastore"
        #files = sorted(os.listdir(path), key=os.path.getmtime)
        mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
        files = list(sorted(os.listdir(path), key=mtime))
        newest = files[-1]
        self.working_dir = self.tmp_dir+'/datastore/'+newest
        path = self.working_dir+'/outputs/cwltool.stdout.txt'
        with open(path) as data_file:
            parsed_json = json.load(data_file)
        for key, value in parsed_json.iteritems():
            print("ITEM: "+key)
            file_map = {}
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    self.fill_in_file_dict(file_map, parsed_json[key])
                    result.append(file_map)
                    file_map = {}
            elif isinstance(value, list):
                for arr_value in parsed_json[key]:
                    if isinstance (arr_value, dict):
                        if arr_value['class'] == 'File':
                            self.fill_in_file_dict(file_map, arr_value)
                            result.append(file_map)
                            file_map = {}
        print(result)
        return(result)

    ''' make a dict of input files '''
    def map_file_inputs(self, json_encoded):
        # this is going to be an array of dicts that can then
        bundle_array = []
        file_map = {}
        decoded = base64.urlsafe_b64decode(json_encoded)
        # this needs to idenitfy anything with redwood:// and transform it to local path. Also need to deal with output paths
        data = json.loads(decoded)
        for key, value in data.iteritems():
            print("ITEM: "+key)
            if key in self.known_inputs:
                if isinstance(value, dict):
                    if data[key]['class'] == 'File':
                        tokens = data[key]['path'].split('/')
                        file_entry = {}
                        file_entry['file_name'] = key
                        file_entry['file_path'] = tokens[-1]
                        file_entry['file_storage_id'] = tokens[-2]
                        file_entry['file_storage_bundle_id'] = tokens[-3]
                        name_tokens = file_entry['file_path'].split('.')
                        file_entry['file_type'] = name_tokens[-1]
                        if file_entry['file_path'].endswith('fastq.gz'):
                            file_entry['file_type'] = 'fastq.gz'
                        # now add this to an array
                        if (tokens[-3] not in file_map.keys()):
                            file_map[tokens[-3]] = []
                        file_map[tokens[-3]].append(file_entry)
                elif isinstance(value, list):
                    for arr_value in data[key]:
                        if isinstance (arr_value, dict):
                            if arr_value['class'] == 'File':
                                tokens = arr_value['path'].split('/')
                                file_entry = {}
                                file_entry['file_name'] = key
                                file_entry['file_path'] = tokens[-1]
                                file_entry['file_storage_id'] = tokens[-2]
                                file_entry['file_storage_bundle_id'] = tokens[-3]
                                name_tokens = file_entry['file_path'].split('.')
                                file_entry['file_type'] = name_tokens[-1]
                                if file_entry['file_path'].endswith('fastq.gz'):
                                    file_entry['file_type'] = 'fastq.gz'
                                # now add this to an array
                                if (tokens[-3] not in file_map.keys()):
                                    file_map[tokens[-3]] = []
                                file_map[tokens[-3]].append(file_entry)
        # now loop through file_arr and build
        for bundle_id in file_map.keys():
            bundle_hash = {}
            bundle_hash['file_storage_bundle_files'] = file_map[bundle_id]
            bundle_hash['file_storage_bundle_id'] = bundle_id
            bundle_array.append(bundle_hash)
        return(bundle_array)

    ''' make a dict of params '''
    def map_params(self, transformed_json_path):
        params_map = {}
        file_map = {}
        with open(transformed_json_path) as data_file:
            data = json.load(data_file)
        for key, value in data.iteritems():
            print("ITEM: "+key)
            if isinstance(value, dict):
                if data[key]['class'] == 'File':
                    file_map[key] = True
            elif isinstance(value, list):
                for arr_value in data[key]:
                    if isinstance (arr_value, dict):
                        if arr_value['class'] == 'File':
                            file_map[key] = True
                    # can scalars be passed as an array or is it only files?
            else: # then it's a scalar?
                params_map[key] = value
        return(params_map, file_map)

    ''' return a local path from a redwood URL '''
    def convert_to_local_path(self, path):
        if path.startswith('redwood://'):
            uri_pieces = path.split("/")
            bundle_uuid = uri_pieces[3]
            file_uuid = uri_pieces[4]
            file_path = uri_pieces[5]
            print("B: "+bundle_uuid+" F: "+file_uuid+" P: "+file_path)
            return(self.tmp_dir+"/"+bundle_uuid+"/"+file_path)
        elif path.startswith('http://') or path.startswith('https://') or path.startswith('s3://') or path.startswith('sftp://') or path.startswith('ftp://'):
            return(path)
        else: # it's a local path, reform to use our upload directory
            uri_pieces = path.split("/")
            file_path = uri_pieces[-1]
            return(self.tmp_dir+"/upload/"+str(self.bundle_uuid)+"/"+file_path)

    ''' downloads the files referenced and makes a new JSON with their paths '''
    def download_and_transform_json(self, json_encoded):
        decoded = base64.urlsafe_b64decode(json_encoded)
        # this needs to idenitfy anything with redwood:// and transform it to local path. Also need to deal with output paths
        parsed_json = json.loads(decoded)
        print("PARSED JSON: "+decoded)
        map_of_redwood_to_local = {}
        # need to track what are inputs, since all inputs are files from redwood they are easy to flag
        self.known_inputs = {}
        for key, value in parsed_json.iteritems():
            print("ITEM: "+key)
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    path = parsed_json[key]['path']
                    print("PATH: "+path)
                    if path.startswith("redwood://"):
                        self.known_inputs[key] = True
                    map_of_redwood_to_local[path] = self.convert_to_local_path(path)
                    parsed_json[key]['path'] = map_of_redwood_to_local[path]
            elif isinstance(value, list):
                for arr_value in parsed_json[key]:
                    if arr_value['class'] == 'File':
                        path = arr_value['path']
                        print("PATH: "+path)
                        if path.startswith("redwood://"):
                            self.known_inputs[key] = True
                        map_of_redwood_to_local[path] = self.convert_to_local_path(path)
                        arr_value['path'] = map_of_redwood_to_local[path]
        f = open(self.tmp_dir+'/updated_sample.json', 'w')
        print(json.dumps(parsed_json), file=f)
        f.close()
        # now download each
        for curr_redwood_url in map_of_redwood_to_local.keys():
            if curr_redwood_url.startswith("redwood://"):
                print("URL: "+curr_redwood_url)
                uri_pieces = curr_redwood_url.split("/")
                bundle_uuid = uri_pieces[3]
                file_uuid = uri_pieces[4]
                file_path = uri_pieces[5]

                cmd = "mkdir -p "+self.tmp_dir
                #create list of individual command 'words' for input to run commmand function
                self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS)

                cmd = "icgc-storage-client download --output-dir {} --object-id {} --output-layout bundle --force".format(self.tmp_dir, file_uuid)
                #create list of individual command 'words' for input to run commmand function
                self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS)

        return(self.tmp_dir+'/updated_sample.json')

    def mkdir_p(self, path):
        """
        mkdir -p
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        return None

    def loadJsonObj(self, fileName):
        """
        Load a json object from a file
        """
        try:
            file = open(fileName, "r")
            object = json.load(file)
            file.close()
        except:
            logging.error("Error loading and parsing {}".format(fileName))
        return object

    def md5sum(self, filename):
        with open(filename, mode='rb') as f:
            d = hashlib.md5()
            for buf in iter(partial(f.read, 128), b''):
                d.update(buf)
            return d.hexdigest()

    def add_to_registration(self, registration, bundle_id, project, file_path,
                        controlled_access):
        access = 'controlled' if controlled_access else 'open'
        registration.write('{}\t{}\t{}\t{}\t{}\n'.format(
            bundle_id, project, file_path, self.md5sum(file_path), access))
          
    def register_manifest(self, redwood_registration_file, metadata_output_dir):
        redwood_upload_manifest_dir = "redwoodUploadManifest"
        counts = {}
        counts["bundlesFound"] = 0
        redwood_upload_manifest = None
        redwood_registration_manifest = os.path.join(metadata_output_dir,
            redwood_registration_file)
        with open(redwood_registration_manifest, 'w') as registration:
            registration.write(
                'gnos_id\tprogram_code\tfile_path\tfile_md5\taccess\n')
            for dir_name, subdirs, files in os.walk(metadata_output_dir):
                if dir_name == metadata_output_dir:
                    continue
                if len(subdirs) != 0:
                    continue
                if "metadata.json" in files:
                    bundleDirFullPath = os.path.join(os.getcwd(), dir_name)
                    logging.debug("found bundle directory at %s"
                                  % (bundleDirFullPath))
                    counts["bundlesFound"] += 1
                    #bundle_metadata = self.loadJsonObj(
                    #    os.path.join(bundleDirFullPath, "metadata.json"))
                    #There is no program in the metadata.json generated. Need to figure out
                    #how to get that...
                    program = self.program_name
                    bundle_uuid = os.path.basename(dir_name)
                    controlled_access = True
                    if redwood_upload_manifest is None:
                        redwood_upload_manifest = os.path.join(
                            metadata_output_dir, redwood_upload_manifest_dir,
                            bundle_uuid)

                    #Register upload
                    for f in files: 
                        file = os.path.join(dir_name, f)
                        self.add_to_registration(registration, bundle_uuid, program,
                                            file, controlled_access)
                else:
                    logging.info("no metadata file found in %s" % dir_name)
                
                logging.info("counts\t%s" % (json.dumps(counts)))
        self.mkdir_p(os.path.dirname(redwood_upload_manifest))
        return redwood_registration_manifest, redwood_upload_manifest
 
    ''' Kick off main analysis '''
    def run(self):
        #Assigning the environmental variables for REDWOOD ENDPOINT (here refered as redwood host),
        #and for the ACCESS_TOKEN (here referred to as redwood token)
        os.environ["ACCESS_TOKEN"] = self.redwood_token
        os.environ["REDWOOD_ENDPOINT"] = self.redwood_host
        print("** DOWNLOAD **")
        d_utc_datetime = datetime.utcnow()
        d_start = time.time()
        # this will download and create a new JSON
        transformed_json_path = self.download_and_transform_json(self.json_encoded)
        d_end = time.time()
        d_utc_datetime_end = datetime.utcnow()
        d_diff = int(d_end - d_start)
        print("START: "+str(d_start)+" END: "+str(d_end)+" DIFF: "+str(d_diff))

        print("** RUN DOCKSTORE TOOL **")
        t_utc_datetime = datetime.utcnow()
        t_start = time.time()

        #set the container's TMPDIR env variable to the same directory as on the host.
        #This ensures the files written by dockstore in creating this container
        #will be in the same directory as those written by the container created
        #by the dockstore command below
        os.environ["TMPDIR"] = self.tmp_dir

        #dockstore should be on the PATH assuming we are running as root as it was
        #installed in /root in the Dockerfile
        print("Installing Dockstore client at root if this is running inside our Docker image")
        cmd = "cp -R /home/ubuntu/.dockstore ./"
        self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS, True)

        print("Calling Dockstore to launch a Dockstore tool")
        cmd = "dockstore " + self.launch_type + " launch --debug --entry "+self.docker_uri+" --json "+transformed_json_path
        self.run_command(cmd, self.MAX_PIPELINE_ATTEMPTS, self.DELAY_IN_SECONDS, cwd=self.tmp_dir)

        t_end = time.time()
        t_utc_datetime_end = datetime.utcnow()
        t_diff = int(t_end - t_start)
        # timing information
        utc_datetime = datetime.utcnow()
        print("TIME: "+str(utc_datetime.isoformat("T")))
        o_diff = int(t_end - d_start)

        print("** UPLOAD **")
        metadata = '''
{
   "version" : "1.0.0",
   "timestamp" : "%s",
   "parent_uuids" : %s,
   "workflow_url" : "%s",
   "workflow_name" : "%s",
   "workflow_version" : "%s",
   "analysis_type" : "%s",
   "bundle_uuid" : "%s",
   "workflow_params" : {
''' % (str(utc_datetime.isoformat("T")), json.dumps(self.parent_uuids.split(",")), self.dockstore_url, self.workflow_name, self.workflow_version, self.workflow_type, self.bundle_uuid)
        i=0
        (params_map, file_input_map) = self.map_params(transformed_json_path)
        params_map_keys = params_map.keys()
        while i<len(params_map_keys):
            metadata += '''"%s": "%s"''' % (params_map_keys[i], params_map[params_map_keys[i]])
            if i < len(params_map.keys()) - 1:
                metadata += ","
            i += 1
        metadata += '''
   },
   "workflow_outputs" : [
   '''
        # TODO: so I can figure these out via the CWL (if explicit outputs, won't work for arrays) or via the output printed to screen for Dockstore
        i=0
        file_output_map = self.map_outputs()
        while i<len(file_output_map):
            metadata += '''{
              "file_path": "%s",
              "file_type": "%s",
              "file_checksum": "%s",
              "file_size": %d
            }
            ''' % (file_output_map[i]['file_path'], file_output_map[i]['file_type'], file_output_map[i]['file_checksum'], file_output_map[i]['file_size'])
            if i < len(file_output_map) - 1:
                metadata += ","
            i += 1
        metadata += '''
   ],
   "workflow_inputs" :
        %s
   ,
''' % (json.dumps(self.map_file_inputs(self.json_encoded)))
        metadata += '''
   "qc_metrics" : {
   },
   "timing_metrics" : {
      "step_timing" : {
         "download" : {
            "start_time_utc" : "%s",
            "stop_time_utc" : "%s",
            "walltime_seconds" : %d
         },
         "tool_run" : {
            "start_time_utc" : "%s",
            "stop_time_utc" : "%s",
            "walltime_seconds" : %d
         }
      },
      "overall_start_time_utc" : "%s",
      "overall_stop_time_utc" : "%s",
      "overall_walltime_seconds" : %d
   },
   "host_metrics" : {
      "vm_instance_type" : "%s",
      "vm_region" : "%s",
      "vm_instance_cores" : %d,
      "vm_instance_mem_gb" : %d,
      "vm_location" : "%s"
   }
}
        ''' % (str(d_utc_datetime.isoformat("T")), str(d_utc_datetime_end.isoformat("T")), d_diff, str(t_utc_datetime.isoformat("T")), str(t_utc_datetime_end.isoformat("T")), t_diff, str(d_utc_datetime.isoformat("T")), str(utc_datetime.isoformat("T")), o_diff, self.vm_instance_type, self.vm_region, self.vm_instance_cores, self.vm_instance_mem_gb, self.vm_location)
        # FIXME: hardcoded instance information
        f = open(self.tmp_dir+'/upload/'+str(self.bundle_uuid)+'/metadata.json', 'w')
        print(metadata, file=f)
        f.close()

        print("Creating upload directories")
        cmd = "mkdir -p %s/upload/%s %s/manifest" % (self.tmp_dir, self.bundle_uuid, self.tmp_dir)
        self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS)

        print("Registering uploads")
#        cmd = "dcc-metadata-client -i %s/upload/%s -o %s/manifest -m manifest.txt" % (self.tmp_dir, self.bundle_uuid, self.tmp_dir)
        #Call method to write manifest.txt to perform the upload
        metadata_output_dir = "%s/upload/" % (self.tmp_dir)
        redwood_registration_manifest, redwood_upload_manifest = self.register_manifest("registration.tsv", metadata_output_dir)
        cmd = "dcc-metadata-client -o %s -m %s" % (os.path.dirname(redwood_upload_manifest), redwood_registration_manifest)
        self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS)

        print("Performing uploads")
        cmd = "icgc-storage-client upload --force --manifest %s" % (redwood_upload_manifest)
        self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS)

        print("Staging metadata.json to be the return file")
        cmd = 'cp '+self.tmp_dir+'/upload/'+str(self.bundle_uuid)+'/metadata.json ./'
        self.run_command(cmd, self.MAX_ATTEMPTS, self.DELAY_IN_SECONDS)

# run the class
if __name__ == '__main__':
    runner = DockstoreRunner()
