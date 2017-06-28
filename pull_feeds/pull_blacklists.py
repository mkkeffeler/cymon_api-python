#Miclain Keffeler
#6/8/2017 
import requests
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy import types
from sqlalchemy import Column, Text, ForeignKey, Integer, String
from optparse import OptionParser
import hashlib
import base64
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from build_database import IP_Current, IP_History
from sqlalchemy import exists
import dateutil.parser
from sqlalchemy.sql.expression import literal_column


def send_request(apiurl, scanurl, headers):   #This function makes a request to the X-Force Exchange API using a specific URL and headers. 
    output = open(sys.argv[2]+".json","w")    #Output all downloaded json to a file
    apiurl = apiurl + "/?offset=0"
    response = requests.get(apiurl, timeout=20)
    all_json = response.json()
    output.write(json.dumps(all_json,indent=4,sort_keys=True))
    return all_json

if __name__ == "__main__":

    token = ""

    headers ={'Content-Type': 'application/json'}
    url = "https://cymon.io"
    post = {"Authorization":"Token" + token}

    parser = OptionParser()
    parser.add_option("--pull", "--pull", dest="s_category" , default="none",
                      help="Categories that can be pulled: malware,botnet,spam,phishing,malicious activity(must be in \"),blacklist, and dnsbl", metavar="listname")                                           #Use this option to check an IP addres
parser.add_option("--max", "--max", dest="s_max" , default="none",
                      help="Max number of IPs to be returned", metavar="max") 

(options, args) = parser.parse_args()


if len(sys.argv[1:]) == 0:
    parser.print_help()


if (options.s_category is not "none"):
    if(options.s_max is not "none"):
        scanurl = str(options.s_max)
        category = str(options.s_category)                         #Categories that can be queried: malware, botnet,spam,phishing,malicious activity, blacklist, and dnsbl
        apiurl = url + "/api/nexus/v2/blacklist/ip/" + category + "/?days=1" +  "&limit=" + scanurl 
        all_json = send_request(apiurl,category+scanurl,headers)
    else:
        scanurl = options.s_category
        apiurl = url + "/api/nexus/v1/blacklist/ip/" + scanurl
        all_json = send_request(apiurl,scanurl,headers)

for IP in all_json['results']:            #Will eventually store addresses
    print IP['addr']







