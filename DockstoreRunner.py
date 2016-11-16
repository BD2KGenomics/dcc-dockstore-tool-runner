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

# TODO:
# Items needed:
# * analysis type
# * workflow name
# * workflow version
# * input_bundle_uuids
# * input_file_uuids
# * host VM type, cloud, region

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
        # get args
        args = parser.parse_args()
        self.redwood_path = args.redwood_path
        self.redwood_host = args.redwood_host
        self.redwood_token = args.redwood_token
        self.json_encoded = args.json_encoded
        self.docker_uri = args.docker_uri
        self.dockstore_url = args.dockstore_url
        self.workflow_name = args.dockstore_uri.split(:)[0]
        self.workflow_version = args.dockstore_uri.split(:)[1]
        self.workflow_type = args.workflow_type
        self.parent_uuids = args.parent_uuid
        self.bundle_uuid = uuid.uuid4()
        # run
        self.run()

    def map_outputs(self):
        # going to need to read from datastore
        # FIXME: if multiple instances of this script run at the same time it will get confused out the output dir
        path = 'datastore'
        files = sorted(os.listdir(path), key=os.path.getmtime)
        newest = files[-1]
        path = 'datastore/'+newest+'/outputs/cwltool.stdout.txt'
        # LEFT OFF WITH: need to parse this JSON file and extract outputs 

    # TODO: this needs to return file_input_map, can drop output map
    def map_params(self, transformed_json_path):
        params_map = {}
        file_input_map = {}
        file_output_map = {}
        with open(transformed_json_path) as data_file:
            data = json.load(data_file)
        for key, value in data.iteritems():
            print "ITEM: "+key
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    file_map[key] = True
            elif isinstance(value, list):
                for arr_value in parsed_json[key]:
                    if isinstance (arr_value, dict):
                        if arr_value['class'] == 'File':
                            file_map[key] = True
                    # can scalars be passed as an array or is it only files?
            else: # then it's a scalar?
                params_map[key] = value
        return(params_map, file_input_map, file_output_map)


    def convert_to_local_path(self, path):
        uri_pieces = path.split("/")
        bundle_uuid = uri_pieces[3]
        file_uuid = uri_pieces[4]
        file_path = uri_pieces[5]
        print "B: "+bundle_uuid+" F: "+file_uuid+" P: "+file_path
        return("./tmp/"+bundle_uuid+"/"+file_path)

    def download_and_transform_json(self, json_encoded):
        decoded = base64.urlsafe_b64decode(json_encoded)
        # this needs to idenitfy anything with redwood:// and transform it to local path. Also need to deal with output paths
        parsed_json = json.loads(decoded)
        print "PARSED JSON: "+decoded
        map_of_redwood_to_local = {}
        for key, value in parsed_json.iteritems():
            print "ITEM: "+key
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    path = parsed_json[key]['path']
                    print "PATH: "+path
                    map_of_redwood_to_local[path] = self.convert_to_local_path(path)
                    parsed_json[key]['path'] = map_of_redwood_to_local[path]
            else: # then assuming it's an array!
                for arr_value in parsed_json[key]:
                    if arr_value['class'] == 'File':
                        path = arr_value['path']
                        print "PATH: "+path
                        map_of_redwood_to_local[path] = self.convert_to_local_path(path)
                        arr_value['path'] = map_of_redwood_to_local[path]
        f = open('updated_sample.json', 'w')
        print >>f, json.dumps(parsed_json)
        f.close()
        # now download each
        for curr_redwood_url in map_of_redwood_to_local.keys():
            print "URL: "+curr_redwood_url
            uri_pieces = curr_redwood_url.split("/")
            bundle_uuid = uri_pieces[3]
            file_uuid = uri_pieces[4]
            file_path = uri_pieces[5]
            cmd = "mkdir -p ./tmp && java -Djavax.net.ssl.trustStore="+self.redwood_path+"/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url=https://"+self.redwood_host+":8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url=https://"+self.redwood_host+":5431 -DaccessToken="+self.redwood_token+" -jar "+self.redwood_path+"/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar download --output-dir ./tmp/ --object-id "+file_uuid+" --output-layout bundle"
            print cmd
            result = subprocess.call(cmd, shell=True)
            print "DOWNLOAD RESULT: "+str(result)
        return('updated_sample.json')

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
        # WALT: this is where we need to integration your work
        cmd = "dockstore tool launch --entry "+self.dockstore_uri+" --json "+transformed_json_path
        print cmd
        # TODO: actually perform this run!!!
        t_end = time.time()
        t_utc_datetime_end = datetime.utcnow()
        t_diff = int(t_end - t_start)
        # timing information
        utc_datetime = datetime.utcnow()
        print "TIME: "+str(utc_datetime.isoformat("T"))

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
''' % (str(utc_datetime.isoformat("T"), self.parent_uuids, self.dockstore_url, self.workflow_name, self.workflow_version, self.workflow_type, self.bundle_uuid)
        i=0
        (params_map, file_input_map, file_output_map) = self.map_params(transformed_json_path)
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
        while i<len(file_output_map.keys()):
            metadata += '''{
              "file_path": "%s",
              "file_type_label": "%s"
            }
            ''' % (<TODO>)
            if i < len(file_output_map.keys()) - 1:
                metadata += ","
            i += 1
        metadata += '''
   ],
   "workflow_inputs" : [
      {
         "file_storage_bundle_files" : ['''
        # TODO: problem is this needs to be done per bundle ID and not all together in one loop!
        # TODO: will need to work with the original input JSON with redwood URLs so I can get the budle/file IDs properly
        # TODO: I don't see a way to find out the metadata.json UUID
        i=0
        # LEFT OFF HERE: need to create a map for output files (from stdout of cwltools) and input files (from original JSON with redwood URLs)
        (params_map, file_input_map, file_output_map) = self.map_params(transformed_json_path)
        while i<len(file_input_map.keys()):
            metadata += '''{
              "file_path": "%s",
              "file_type_label": "%s",
              "file_storage_uri" : "%s"
            }
            ''' % (<TODO>)
            if i < len(file_input_map.keys()) - 1:
                metadata += ","
            i += 1
        metadata += '''
         ],
         "file_storage_bundle_uri" : "%s"
      }
   ],
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
        ''' % (<TODO>)
        f = open('metadata.json', 'w')
        print >>f, metadata
        f.close()

        # now perform the upload
        cmd = '''
mkdir -p %s/%s/upload/%s %s/%s/manifest/%s && \
echo "Register Uploads:" && \
java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dserver.baseUrl=%s:8444 -DaccessToken=`cat %s/accessToken` -jar %s/dcc-metadata-client-0.0.16-SNAPSHOT/lib/dcc-metadata-client.jar -i %s/%s/upload/%s -o %s/%s/manifest/%s -m manifest.txt && \
echo "Performing Uploads:" && \
java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url=%s:8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url=%s:5431 -DaccessToken=`cat %s/accessToken` -jar %s/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar upload --force --manifest %s/%s/manifest/%s/manifest.txt
        ''' % (<TODO>)
        print "CMD: "+cmd
        result = subprocess.call(cmd, shell=True)
        if result == 0:
            cmd = "rm -rf "+self.data_dir+"/"+self.bundle_uuid+"/bamstats_report.zip "+self.data_dir+"/"+self.bundle_uuid+"/datastore/"
            print "CLEANUP CMD: "+cmd
            result = subprocess.call(cmd, shell=True)
            if result == 0:
                print "CLEANUP SUCCESSFUL"
            f = self.output().open('w')
            print >>f, "uploaded"
            f.close()

# run the class
if __name__ == '__main__':
    runner = DockstoreRunner()
