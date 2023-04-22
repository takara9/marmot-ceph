#!/bin/python3
import json,sys,re
lines = json.load(sys.stdin)
for line in lines:
    m = re.search("Password: \w+", line)
    if m != None:
        p = re.search(r"(?<=\s)\w+", m.group())
        print(p.group())
