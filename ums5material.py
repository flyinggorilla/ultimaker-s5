import requests
from requests.auth import HTTPDigestAuth
import os.path
import yaml # pip install pyyaml
import json
import untangle

## pip install untangle

## default config, override by creating  ums5material.config.yaml or specify authentication and url options 
config = {"id" : "", "key" : "", "hostname" : "ultimaker"}

try:
    config = yaml.load(open('ums5material.config.yaml'), Loader=yaml.FullLoader)
except Exception as ex:
    print(ex)
    print("WARNING: 'ums5material.config.yaml' not found.\nConsider using -s option to create .config.yaml file to store id, key, hostname and more....")

api_id = config["id"]
api_key = config["key"]
hostname = config["hostname"]
filename = None

# post material
def PostMaterial(hostname, id, key, filepath):
    filename = os.path.basename(filepath)
    f = {'file': (filename, open(filepath, "rb"), "text/xml")}
    r = requests.post("http://%s/api/v1/materials" % hostname, 
        files = f, auth = HTTPDigestAuth(id, key))
    print("Posted %s: %d %s" % (filepath, r.status_code, r.text))


def ReadMetadata(filepath):
    with open(filepath, "r", encoding = "utf-8") as f:
        materialxml = f.read()
        metadata = {}

        u = untangle.parse(materialxml)
        metadata["brand"] = u.fdmmaterial.metadata.name.brand.cdata
        metadata["material"] = u.fdmmaterial.metadata.name.material.cdata
        metadata["color"] = u.fdmmaterial.metadata.name.color.cdata
        metadata["guid"] = u.fdmmaterial.metadata.GUID.cdata
        if hasattr(u.fdmmaterial.metadata.name, "label"):
            metadata["label"] = u.fdmmaterial.metadata.name.label.cdata
        else:
            metadata["label"] = ""
        print("Material found: %s %s %s %s %s" % (metadata["brand"], metadata["material"], 
            metadata["label"], metadata["color"], metadata["guid"]))
        
        #print(u.fdmmaterial.settings.machine)
        #ums5 = False
        #wrongCuraExport = ""
        #for m in u.fdmmaterial.settings.machine:
        #    if m.machine_identifier["product"] == "Ultimaker S5":
        #        ums5 = True
        #    if m.machine_identifier["product"] == "ultimaker_s5":
        #        wrongCuraExport = "\nCura material export detected, change 'ultimaker_s5' to 'Ultimaker S5'"
        #    #print(m.machine_identifier["product"])
        #
        #if not ums5:
        #    quit("ERROR: No compatible machine setting in %s detected. product attribute must be 'Ultimaker S5'. %s" % (filepath, wrongCuraExport))

        return metadata

def ReadGuid(filepath):
    return ReadMetadata(filepath)["guid"]

def DeleteMaterial(hostname, id, key, filepath="", guid=None):
    if guid == None:
        guid = ReadGuid(filepath)

    r = requests.delete("http://%s/api/v1/materials/%s" % (hostname, guid), 
        auth = HTTPDigestAuth(api_id, api_key))

    print("Deleted %s: %d %s" % (filepath, r.status_code, r.text))


def UpdateMaterial(hostname, id, key, filepath = "", guid = None):
    DeleteMaterial(hostname, id, key, filepath, guid)
    PostMaterial(hostname, id, key, filepath)

def ListMaterials(hostname, filter=None):
    r = requests.get("http://%s/api/v1/materials" % hostname)
    j = r.json()
    #print(r.json())

    for l in j:
        #print(l)
        u = untangle.parse(l)
        brand = u.fdmmaterial.metadata.name.brand.cdata
        material = u.fdmmaterial.metadata.name.material.cdata
        color = u.fdmmaterial.metadata.name.color.cdata
        guid = u.fdmmaterial.metadata.GUID.cdata
        if hasattr(u.fdmmaterial.metadata.name, "label"):
            label = u.fdmmaterial.metadata.name.label.cdata
        else:
            label = ""
        if filter:
            if filter not in brand and filter not in material and filter not in color and filter not in guid and filter not in label: 
                continue
        print("Material: %s, %s, %s, %s, %s" % (brand, material, label, color, guid))
        #f = open("fromprinter/ums5materials.fromprinter %s %s %s %s.xml" % (brand, label, material, color) , "wb")
        #f.write(l.encode("utf-8"))
        #f.close()

def CreateAuthKeys(hostname, application, user):
    import requests

    r = requests.post("http://%s/api/v1/auth/request" % hostname, { "application" : application, "user" : user})
    if r.status_code != 200:
        print("Error creating keys for %s and user %s. %d %s" % (application, user, r.status_code, r.text))
        return None
    j = r.json()
    api_id = j["id"]
    api_key = j["key"]
    print("Keys generated: ID:KEY=%s:%s %d %s" % (api_id, api_key, r.status_code, r.text))
    print('Please accept request on Ultimaker S5 display for application "%s" and user "%s" to use keys.' % (application, user))
    return (api_id, api_key)

def VerifyAuth(hostname, id, key):
    r = requests.get("http://ultimaker.linz.local/api/v1/auth/verify", auth = HTTPDigestAuth(id, key))
    print("Verify authentication: %d %s" % (r.status_code, r.text))

from optparse import OptionParser

usage = "usage: %prog [options] [ultimaker-url] [material-filename]"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename", metavar="FILE", help="Ultimaker S5 material XML file")
parser.add_option("-u", "--update",
                  action="store_true", dest="update", default=False,
                  help="udpate to printer")
parser.add_option("-l", "--list", dest="list", action="store_true", default=False, help="List materials on Ultimaker S5, provide optional --filter string")
parser.add_option("-F", "--filter", dest="filter", default=None, help="Filters listed materials filter string")
parser.add_option("-g", "--guid", dest="guid", default=None, help="GUID of material", metavar="<guid>")
parser.add_option("-a", "--auth", dest="auth", default=None, help="digest authentication", metavar="<id>:<key>")
parser.add_option("-s", "--storeconfig", dest="storeconfig", default=False, action="store_true", help="store given host and authentication information to config file.")
parser.add_option("-C", "--createauth", dest="createauth", default=False, action="store_true", help="create ID:KEY authentication credentials writing/deleting materials. Please make sure to accept authorization request on Ultimaker S5 printer display.")
parser.add_option("-v", "--verifyauth", dest="verifyauth", default=False, action="store_true", help="Verify whether authentication against Ultimaker S5 REST api succeeds with provided ID/KEY.")
parser.add_option("-d", "--delete",
                  action="store_true", dest="delete", default=False,
                  help="delete material from printer with -g GUID or guid is extracted from material xml file")
(options, args) = parser.parse_args()

for arg in args:
    from urllib.parse import urlparse
    o = urlparse(arg)
    if o.scheme == "http":
        hostname = o.hostname
        print("Ultimaker S5 hostname: %s" % hostname)
        config["hostname"] = hostname
    elif arg[-13:] == ".fdm_material":
        filename = arg
        print("Material filename: %s" % filename)

if options.auth:
    a = options.auth.split(":")
    if len(a) != 2:
        parser.error("invalid authentication string. please provide <id>:<key>.")
    config["id"]  = api_id  = a[0]
    config["key"] = api_key = a[1]

help = True
if options.createauth:
    import getpass
    keys = CreateAuthKeys(hostname, __file__, getpass.getuser())
    if keys:
        config["id"] = keys[0]
        config["key"] = keys[1]
    help = False

if options.verifyauth:
    VerifyAuth(hostname, api_id, api_key)
    help = False

elif options.update:
    if not filename:
        parser.error("Please provide material filename")
    print("Contacting Ultimaker S5 at %s with ID %s" % (hostname, api_id))
    UpdateMaterial(hostname, api_id, api_key, filename)
    help = False

elif options.list and hostname:
    ListMaterials(hostname, options.filter)
    help = False

elif options.delete:
    guid = options.guid
    if not hostname or len(hostname) < 3:
        parser.error("Please provide URL or hostname in config.yaml")
    if not guid:
        if filename:
            guid = ReadGuid(filename)
            if not guid:
                parser.error("No guid found in %s" % filename)
        else:
            parser.error("Please provide material -g GUID or material filename that indirectly provides the GUID from the xml")

    DeleteMaterial(hostname, api_id, api_key, guid=guid)
    help = False

elif filename:
    md = ReadMetadata(filename)
    help = False

if options.storeconfig:
    yaml.dump(config, open("ums5material.config.yaml", "w"), default_flow_style = False)
    print("stored config to ums5material.config.yaml")
    help = False

if help:
    parser.print_help()
        

