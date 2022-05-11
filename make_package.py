import requests
import json
import os
import sys
from datetime import datetime

file = f"{datetime.now().strftime('%Y%m%d_%H%M')}.tar"
bfile = file.replace('.tar','.BIN')
cmd=f'tar cf {file}'
for f in sys.argv:
    if f == 'make_package.py': continue
    cmd += f' {f}'
print(cmd)
os.system(cmd)
os.system(f'openssl aes-256-cbc -pbkdf2 -in {file} -out {bfile}')
print(f'openssl aes-256-cbc -pbkdf2 -in {file} -out {bfile}')
os.system(f'rcp {bfile} ubuntu@damoa.io:Web/public/update')
print(f'rcp {bfile} ubuntu@damoa.io:Web/public/update')
