import json
import time
import re
from datetime import datetime
import subprocess
import argparse
import base64
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
        parser.add_argument('--dockstore-uri', default='quay.io/wshands/fastqc', required=True)
        parser.add_argument('--parent-uuid', default='parent-UUID-dummy-value', required=True)
        #parser.add_argument('--parent-uuid', default='parent-UUID-dummy-value', action='append', required=True)
        # get args
        args = parser.parse_args()
        self.redwood_path = args.redwood_path
        self.redwood_host = args.redwood_host
        self.redwood_token = args.redwood_token
        self.json_encoded = args.json_encoded
        self.dockstore_uri = args.dockstore_uri
        self.parent_uuids = args.parent_uuid
        # run
        self.run()

    def map_params(self, transformed_json_path):
        params_map = {}
        file_map = {}
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
        return(params_map, file_map)


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
   "workflow_bundle_url" : "%s",
   "workflow_name" : "%s"
   "workflow_params" : {
'''
        i=0
        (params_map, file_map) = self.map_params(transformed_json_path)
        while i<len(params_map.keys()):
            metadata += '''"%s": "%s"'''
            if i < len(params_map.keys()) - 1:
                metadata += ","
            i += 1
        metadata += '''
   },
   "workflow_outputs" : {
   '''

        i=0
        (params_map, file_map) = self.map_params(transformed_json_path)
        while i<len(params_map.keys()):
            metadata += '''
            "%s": "%s"

            '''
            if i < len(params_map.keys()) - 1:
                metadata += ","
            i += 1

      "foo.bam.bai" : {
         "file_type_label" : "bai",
         "file_type_cv_terms" : [
            "EDAM:278392"
         ]
      },
      "foo.bam" : {
         "file_type_label" : "bam",
         "file_type_cv_terms" : [
            "EDAM:1293829"
         ]
      }

      metadata += '''
   },
   "workflow_inputs" : [
      {
         "file_storage_bundle_files" : {
            "foo1.fastq.gz" : {
               "file_storage_uri" : "ae616ade-3734-4c48-a609-f2b292ecdbc7",
               "file_type_label" : "fastq",
               "file_type_cv_terms" : [
                  "EDAM:123232"
               ]
            },
            "foo2.fastq.gz" : {
               "file_type_label" : "fastq",
               "file_type_cv_terms" : [
                  "EDAM:123232"
               ],
               "file_storage_uri" : "9014505b-fa59-4913-a05c-4666c6efe198"
            }
         },
         "file_storage_metadata_json_uri" : "153c380c-0bcb-4ee9-abdf-629db73a62e5",
         "file_storage_bundle_uri" : "0e99945c-631e-4123-9158-5132a8fe2150"
      }
   ],
   "workflow_version" : "%s",
   "qc_metrics" : {
   },
   "timing_metrics" : {
      "step_timing" : {
         "alignment" : {
            "stop_time_utc" : "Thu Apr 14 24:18:30 UTC 2016",
            "walltime_seconds" : 60000,
            "start_time_utc" : "Thu Apr 14 22:18:30 UTC 2016"
         }
      },
      '''
        metadata += '''
      "overall_stop_time_utc" : "%s",
      "overall_start_time_utc" : "%s",
      "overall_walltime_seconds" : %s
   },
   "host_metrics" : {
      "vm_instance_type" : "m1.xlarge",
      "vm_region" : "us-east-1",
      "vm_instance_cores" : 4,
      "vm_instance_mem_gb" : 256,
      "vm_location" : "aws"
   }
}
        '''


        # TODO: need to iterate over the outputs, prepare upload, perform upload, cleanup
#        cmd = '''mkdir -p %s/%s/upload/%s %s/%s/manifest/%s && ln -s %s/%s/bamstats_report.zip %s/%s/metadata.json %s/%s/upload/%s && \
#echo "Register Uploads:" && \
#java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dserver.baseUrl=%s:8444 -DaccessToken=`cat %s/accessToken` -jar %s/dcc-metadata-client-0.0.16-SNAPSHOT/lib/dcc-metadata-client.jar -i %s/%s/upload/%s -o %s/%s/manifest/%s -m manifest.txt && \
#echo "Performing Uploads:" && \
#java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url=%s:8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url=%s:5431 -DaccessToken=`cat %s/accessToken` -jar %s/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar upload --force --manifest %s/%s/manifest/%s/manifest.txt
#''' % (self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.data_dir, self.bundle_uuid, self.tmp_dir, self.bundle_uuid, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.ucsc_storage_client_path, self.ucsc_storage_host, self.ucsc_storage_client_path, self.ucsc_storage_client_path, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.ucsc_storage_client_path, self.ucsc_storage_host, self.ucsc_storage_host, self.ucsc_storage_client_path, self.ucsc_storage_client_path, self.tmp_dir, self.bundle_uuid, self.upload_uuid)
        #
#        print "CMD: "+cmd
#        result = subprocess.call(cmd, shell=True)
#        if result == 0:
#            cmd = "rm -rf "+self.data_dir+"/"+self.bundle_uuid+"/bamstats_report.zip "+self.data_dir+"/"+self.bundle_uuid+"/datastore/"
#            print "CLEANUP CMD: "+cmd
#            result = subprocess.call(cmd, shell=True)
#            if result == 0:
#                print "CLEANUP SUCCESSFUL"
#            f = self.output().open('w')
#            print >>f, "uploaded"
#            f.close()

    def output(self):
        return luigi.LocalTarget(self.tmp_dir+"/"+self.bundle_uuid+"/"+self.filename)

# run the class
if __name__ == '__main__':
    runner = DockstoreRunner()
