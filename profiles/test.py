import json
from StringIO import StringIO

f = StringIO("replicatorDual.json")
print json.load(f)
