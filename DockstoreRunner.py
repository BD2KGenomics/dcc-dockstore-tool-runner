""" 
    author Brian O'Conner 
    broconno@ucsc.com 
        


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

import os
import sys

# TODO:
# Items needed:
# * analysis type
# * workflow name
# * workflow version
# * input_bundle_uuids
# * input_file_uuids
# * host VM type, cloud, region
# * I need better code for determining the output path used for downloads...e.g. don't just use tmp

class DockstoreRunner:

    def __init__(self):
        parser = argparse.ArgumentParser(description='Downloads, runs tool via Dockstore, then uploads results.')
        parser.add_argument('--redwood-path', default='/usr/local/ucsc-storage-client', required=False)
        parser.add_argument('--redwood-token', default='token-UUID-dummy-value', required=True)
        parser.add_argument('--redwood-host', default='storage.ucsc-cgl.org', required=True)
        parser.add_argument('--json-encoded', default='e30=', required=True)
        parser.add_argument('--docker-uri', default='quay.io/wshands/fastqc:latest', required=True)
        parser.add_argument('--dockstore-url', default='https://dockstore.org/containers/quay.io/wshands/fastqc', required=True)
        parser.add_argument('--workflow-type', default='qc', required=True)
        parser.add_argument('--parent-uuid', default='parent-UUID-dummy-value', required=True)
        # FIXME: this append seems to crash on the mac but it would be the way to go if we want multiple parents
        #parser.add_argument('--parent-uuid', default='parent-UUID-dummy-value', action='append', required=True)
        parser.add_argument('-d', '--tmpdir', type=str, required=True,
                        help="Path to tmpdir, e.g. /path/to/temporary directory for"
                        " container to write intermediate files.")
        # get args
        args = parser.parse_args()
        self.redwood_path = args.redwood_path
        self.redwood_host = args.redwood_host
        self.redwood_token = args.redwood_token
        self.json_encoded = args.json_encoded
        self.docker_uri = args.docker_uri
        self.dockstore_url = args.dockstore_url
        self.workflow_name = args.docker_uri.split(':')[0]
        self.workflow_version = args.docker_uri.split(':')[1]
        self.workflow_type = args.workflow_type
        self.parent_uuids = args.parent_uuid
        self.bundle_uuid = uuid4()
        #self.tmp_dir = './datastore-tool-launcher'
        self.tmpdir = args.tmpdir
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        if not os.path.exists(self.tmp_dir+"/upload/"+str(self.bundle_uuid)):
            os.makedirs(self.tmp_dir+"/upload/"+str(self.bundle_uuid))
        # run
        self.run()

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
        path = 'datastore'
        #files = sorted(os.listdir(path), key=os.path.getmtime)
        mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
        files = list(sorted(os.listdir(path), key=mtime))
        newest = files[-1]
        self.working_dir = 'datastore/'+newest
        path = 'datastore/'+newest+'/outputs/cwltool.stdout.txt'
        with open(path) as data_file:
            parsed_json = json.load(data_file)
        for key, value in parsed_json.iteritems():
            print "ITEM: "+key
            file_map = {}
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    self.fill_in_file_dict(file_map, parsed_json)
                    result.append(file_map)
                    file_map = {}
            elif isinstance(value, list):
                for arr_value in parsed_json[key]:
                    if isinstance (arr_value, dict):
                        if arr_value['class'] == 'File':
                            self.fill_in_file_dict(file_map, arr_value)
                            result.append(file_map)
                            file_map = {}
        print result
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
            print "ITEM: "+key
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
            print "ITEM: "+key
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
            print "B: "+bundle_uuid+" F: "+file_uuid+" P: "+file_path
            return(self.tmp_dir+"/"+bundle_uuid+"/"+file_path)
        else: # it's a local path, reform to use our upload directory
            uri_pieces = path.split("/")
            file_path = uri_pieces[-1]
            return(self.tmp_dir+"/upload/"+str(self.bundle_uuid)+"/"+file_path)

    ''' downloads the files referenced and makes a new JSON with their paths '''
    def download_and_transform_json(self, json_encoded):
        decoded = base64.urlsafe_b64decode(json_encoded)
        # this needs to idenitfy anything with redwood:// and transform it to local path. Also need to deal with output paths
        parsed_json = json.loads(decoded)
        print "PARSED JSON: "+decoded
        map_of_redwood_to_local = {}
        # need to track what are inputs, since all inputs are files from redwood they are easy to flag
        self.known_inputs = {}
        for key, value in parsed_json.iteritems():
            print "ITEM: "+key
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    path = parsed_json[key]['path']
                    print "PATH: "+path
                    if path.startswith("redwood://"):
                        self.known_inputs[key] = True
                    map_of_redwood_to_local[path] = self.convert_to_local_path(path)
                    parsed_json[key]['path'] = map_of_redwood_to_local[path]
            else: # then assuming it's an array!
                for arr_value in parsed_json[key]:
                    if arr_value['class'] == 'File':
                        path = arr_value['path']
                        print "PATH: "+path
                        if path.startswith("redwood://"):
                            self.known_inputs[key] = True
                        map_of_redwood_to_local[path] = self.convert_to_local_path(path)
                        arr_value['path'] = map_of_redwood_to_local[path]
        f = open(self.tmp_dir+'/updated_sample.json', 'w')
        print >>f, json.dumps(parsed_json)
        f.close()
        # now download each
        for curr_redwood_url in map_of_redwood_to_local.keys():
            if curr_redwood_url.startswith("redwood://"):
                print "URL: "+curr_redwood_url
                uri_pieces = curr_redwood_url.split("/")
                bundle_uuid = uri_pieces[3]
                file_uuid = uri_pieces[4]
                file_path = uri_pieces[5]
                cmd = "mkdir -p "+self.tmp_dir+" && java -Djavax.net.ssl.trustStore="+self.redwood_path+"/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url=https://"+self.redwood_host+":8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url=https://"+self.redwood_host+":5431 -DaccessToken="+self.redwood_token+" -jar "+self.redwood_path+"/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar download --output-dir "+self.tmp_dir+" --object-id "+file_uuid+" --output-layout bundle"
                print cmd
                result = subprocess.call(cmd, shell=True)
                print "DOWNLOAD RESULT: "+str(result)
        return(self.tmp_dir+'/updated_sample.json')

    ''' Kick off main analysis '''
    def run(self):
        print "** DOWNLOAD **"
        d_utc_datetime = datetime.utcnow()
        d_start = time.time()
        # this will download and create a new JSON
        transformed_json_path = self.download_and_transform_json(self.json_encoded)
        d_end = time.time()
        d_utc_datetime_end = datetime.utcnow()
        d_diff = int(d_end - d_start)
        print "START: "+str(d_start)+" END: "+str(d_end)+" DIFF: "+str(d_diff)

        print "** RUN DOCKSTORE TOOL **"
        t_utc_datetime = datetime.utcnow()
        t_start = time.time()

        #cmd = "dockstore tool launch --entry "+self.docker_uri+" --json "+transformed_json_path
        #print cmd
        #result = subprocess.call(cmd, shell=True)

        #set the container's TMPDIR env variable to the same directory as on the host.
        #This ensures the files written by dockstore in creating this container
        #will be in the same directory as those written by the container created
        #by the dockstore command below
        os.environ["TMPDIR"] = self.tmpdir
   
        #dockstore should be on the PATH assuming we are running as root as it was
        #installed in /root in the Dockerfile
        cmd = ["dockstore", "tool", "launch", "--debug", "--entry", self.dockstore_uri, "--json", transformed_json_path]
        #TODO: put try catch block around suprocess.call to cleanup and print
        #error messages?
        print cmd
        result = subprocess.call(cmd)
        if result != 0:
            print "ERRORS running dockstore CMD!!!"
        else:
            print "DOCKSTORE CMD SUCCESSFUL!!"

        t_end = time.time()
        t_utc_datetime_end = datetime.utcnow()
        t_diff = int(t_end - t_start)
        # timing information
        utc_datetime = datetime.utcnow()
        print "TIME: "+str(utc_datetime.isoformat("T"))
        o_diff = int(t_end - d_start)

        print "** UPLOAD **"
        metadata = '''
{
   "version" : "1.0.0",
   "timestamp" : "%s",
   "parent_uuids" : [
      "%s"
   ],
   "workflow_url" : "%s",
   "workflow_name" : "%s",
   "workflow_version" : "%s",
   "analysis_type" : "%s",
   "bundle_uuid" : "%s",
   "workflow_params" : {
''' % (str(utc_datetime.isoformat("T")), self.parent_uuids, self.dockstore_url, self.workflow_name, self.workflow_version, self.workflow_type, self.bundle_uuid)
        i=0
        (params_map, file_input_map) = self.map_params(transformed_json_path)
        while i<len(params_map.keys()):
            metadata += '''"%s": "%s"'''
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
            "stop_time_utc" : "%s",
            "walltime_seconds" : %d,
            "start_time_utc" : "%s"
         },
         "tool_run" : {
            "stop_time_utc" : "%s",
            "walltime_seconds" : %d,
            "start_time_utc" : "%s"
         }
      },
      "overall_stop_time_utc" : "%s",
      "overall_start_time_utc" : "%s",
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
        ''' % (str(d_utc_datetime.isoformat("T")), d_diff, str(d_utc_datetime_end.isoformat("T")), str(t_utc_datetime.isoformat("T")), t_diff, str(t_utc_datetime_end.isoformat("T")), str(utc_datetime.isoformat("T")), str(d_utc_datetime.isoformat("T")), o_diff, 'm4.4xlarge', 'us-west-2', 16, 64, 'aws')
        # FIXME: hardcoded instance information
        f = open(self.tmp_dir+'/upload/'+str(self.bundle_uuid)+'/metadata.json', 'w')
        print >>f, metadata
        f.close()

        # now perform the upload
        cmd = '''
mkdir -p %s/upload/%s %s/manifest && \
echo "Register Uploads:" && \
java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dserver.baseUrl=https://%s:8444 -DaccessToken=%s -jar %s/dcc-metadata-client-0.0.16-SNAPSHOT/lib/dcc-metadata-client.jar -i %s/upload/%s -o %s/manifest -m manifest.txt && \
echo "Performing Uploads:" && \
java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url=https://%s:8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url=https://%s:5431 -DaccessToken=%s -jar %s/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar upload --force --manifest %s/manifest/manifest.txt
#        ''' % (self.tmp_dir, self.bundle_uuid, self.tmp_dir, self.redwood_path, self.redwood_host, self.redwood_token, self.redwood_path, self.tmp_dir, self.bundle_uuid, self.tmp_dir, self.redwood_path, self.redwood_host, self.redwood_host, self.redwood_token, self.redwood_path, self.tmp_dir)
        print "CMD: "+cmd
        result = subprocess.call(cmd, shell=True)
        if result != 0:
            print "ERRORS UPLOADING!!"
#        else:
#            cmd = "rm -rf "+self.data_dir+"/"+self.bundle_uuid+"/bamstats_report.zip "+self.data_dir+"/"+self.bundle_uuid+"/datastore/"
#            print "CLEANUP CMD: "+cmd
#            result = subprocess.call(cmd, shell=True)
#            if result == 0:
#                print "CLEANUP SUCCESSFUL"
#            f = self.output().open('w')
#            print >>f, "uploaded"
#            f.close()

# run the class
if __name__ == '__main__':
    runner = DockstoreRunner()
