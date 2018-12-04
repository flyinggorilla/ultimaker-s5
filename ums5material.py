import requests
from requests.auth import HTTPDigestAuth
import os.path
import yaml
import json
import untangle

config = {"id" : "", "key" : "", "hostname" : "ultimaker"}

try:
    config = yaml.load(open('config.yaml'))
except:
    print("WARNING: 'config.yaml' not found.\nConsider creating config.yaml file to store id, key, hostname and more....")

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
    print("Posted %s %d %s " % (filepath, r.status_code, r.text))


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
            label = ""
        print("Material found: %s %s %s %s {%s}" % (metadata["brand"], metadata["material"], 
            metadata["label"], metadata["color"], metadata["guid"]))
        
        #print(u.fdmmaterial.settings.machine)
        ums5 = False
        wrongCuraExport = ""
        for m in u.fdmmaterial.settings.machine:
            if m.machine_identifier["product"] == "Ultimaker S5":
                ums5 = True
            if m.machine_identifier["product"] == "ultimaker_s5":
                wrongCuraExport = "\nCura material export detected, change 'ultimaker_s5' to 'Ultimaker S5'"
            #print(m.machine_identifier["product"])

        if not ums5:
            quit("ERROR: No compatible machine setting in %s detected. product attribute must be 'Ultimaker S5'. %s" % (filepath, wrongCuraExport))

        return metadata

def ReadGuid(filepath):
    return ReadMetadata(filepath)["guid"]

def DeleteMaterial(hostname, id, key, filepath="", guid=None):
    if guid == None:
        guid = ReadGuid(filepath)

    r = requests.delete("http://%s/api/v1/materials/%s" % (hostname, guid), 
        auth = HTTPDigestAuth(api_id, api_key))

    print("Deleted %s %d %s " % (filepath, r.status_code, r.text))


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


from optparse import OptionParser

usage = "usage: %prog [options] [ultimaker-url] [material-filename]"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename", metavar="FILE", help="Ultimaker S5 material XML file")
#parser.add_option("-hn", "--hostname", dest="hostname", help="Ultimaker S5 hostname or IP address")
parser.add_option("-u", "--update",
                  action="store_true", dest="update", default=False,
                  help="udpate to printer")
parser.add_option("-l", "--list", dest="list", action="store_true", default=False, help="List materials on Ultimaker S5, provide optional --filter string")
parser.add_option("-F", "--filter", dest="filter", default=None, help="Filters listed materials filter string")
parser.add_option("-g", "--guid", dest="guid", default=None, help="GUID of material", metavar="<guid>")
parser.add_option("-a", "--auth", dest="auth", default=None, help="digest authentication", metavar="<id>:<key>")
parser.add_option("-C", "--createauth", dest="createauth", default=False, metavar="<application>:<user>", help="create ID:KEY authentication credentials writing/deleting materials. application is Name of the application that wants access. Displayed to the user. Name of the user who wants access. Displayed to the user when confirming access.")
parser.add_option("-d", "--delete",
                  action="store_true", dest="delete", default=False,
                  help="delete material from printer with -g GUID or guid is extracted from material xml file")
(options, args) = parser.parse_args()
#if len(args) != 1:
    #parser.print_help()
    #parser.error("invalid...")
    #quit()

from urllib.parse import urlparse


for arg in args:
    o = urlparse(arg)
    if o.scheme == "http":
        hostname = o.hostname
        print("Ultimaker S5 hostname: %s" % hostname)
    elif arg[-13:] == ".fdm_material":
        filename = arg
        print("Material filename: %s" % filename)

if options.update:
    if not filename:
        parser.error("Please provide material filename")
    print("Contacting Ultimaker S5 at %s with ID %s" % (hostname, api_id))
    UpdateMaterial(hostname, api_id, api_key, filename)
elif options.filter and hostname:
    ListMaterials(hostname, options.filter)
elif filename:
    md = ReadMetadata(filename)
elif hostname and options.list:
    ListMaterials(hostname)
elif hostname and options.delete and options.guid:
    DeleteMaterial(hostname, api_id, api_key, guid=options.guid)
else:
    parser.print_help()
        
#TODO
# check whether product="Ultimaker S5" ... cura export creates wrong product string