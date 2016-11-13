import json
import time
import re
import datetime
import subprocess
import argparse
import base64
from urllib import urlopen
from uuid import uuid4

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

    def download_and_transform_json(self, json_encoded):
        decoded = base64.urlsafe_b64decode(json_encoded)
        # TODO: so this needs to idenitfy anything with redwood:// and transform it to local path. Also need to deal with output paths
        parsed_json = json.loads(decoded)
        print "PARSED JSON: "+decoded
        for key, value in parsed_json.iteritems():
            print "ITEM: "+key
            if isinstance(value, dict):
                if parsed_json[key]['class'] == 'File':
                    path = parsed_json[key]['path']
                    print "PATH: "+path
            else:
                for arr_value in parsed_json[key]:
                    path = arr_value['path']
                    print "PATH: "+path
        #for curr_uuid in self.
        # LEFT OFF HERE
        # foreach, download
        #cmd = "java -Djavax.net.ssl.trustStore="+self.redwood_path+"/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url="+self.redwood_host+":8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url="+self.redwood_host+":5431 -DaccessToken="+self.redwood_token+" -jar "+self.redwood_path+"/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar download --output-dir ./ --object-id "+self.uuid+" --output-layout bundle"
        #print cmd
#        result = subprocess.call(cmd, shell=True)
#        print "DOWNLOAD RESULT: "+str(result)
#        if result == 0:
#            p = self.output().open('w')
#            print >>p, "finished downloading"
#            p.close()
#        # update JSON structure
#        # write out new JSON file and return path

    def run(self):
        print "** DOWNLOAD **"
        # this will download and create a new JSON
        transformed_json_path = self.download_and_transform_json(self.json_encoded)

#        print "** RUN DOCKSTORE TOOL **"
#        cmd = "dockstore tool run --json "+transformed_json_path+" --other args "
#        print cmd
#
#        print "** UPLOAD **"
#        # TODO: need to iterate over the outputs, prepare upload, perform upload, cleanup
#        cmd = '''mkdir -p %s/%s/upload/%s %s/%s/manifest/%s && ln -s %s/%s/bamstats_report.zip %s/%s/metadata.json %s/%s/upload/%s && \
#echo "Register Uploads:" && \
#java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dserver.baseUrl=%s:8444 -DaccessToken=`cat %s/accessToken` -jar %s/dcc-metadata-client-0.0.16-SNAPSHOT/lib/dcc-metadata-client.jar -i %s/%s/upload/%s -o %s/%s/manifest/%s -m manifest.txt && \
#echo "Performing Uploads:" && \
#java -Djavax.net.ssl.trustStore=%s/ssl/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Dmetadata.url=%s:8444 -Dmetadata.ssl.enabled=true -Dclient.ssl.custom=false -Dstorage.url=%s:5431 -DaccessToken=`cat %s/accessToken` -jar %s/icgc-storage-client-1.0.14-SNAPSHOT/lib/icgc-storage-client.jar upload --force --manifest %s/%s/manifest/%s/manifest.txt
#''' % (self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.data_dir, self.bundle_uuid, self.tmp_dir, self.bundle_uuid, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.ucsc_storage_client_path, self.ucsc_storage_host, self.ucsc_storage_client_path, self.ucsc_storage_client_path, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.tmp_dir, self.bundle_uuid, self.upload_uuid, self.ucsc_storage_client_path, self.ucsc_storage_host, self.ucsc_storage_host, self.ucsc_storage_client_path, self.ucsc_storage_client_path, self.tmp_dir, self.bundle_uuid, self.upload_uuid)
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
