# AioMDA
Message Delivery Agent with modules that can be activated separately. This script is under developpement.

This python script needs to work:
* python in version 3.4 at least
* the module aiosmtpd:
https://github.com/aio-libs/aiosmtpd
http://aiosmtpd.readthedocs.io/en/latest/
* depending on the configuration :
    - the module ldap3 for python3:
http://ldap3.readthedocs.io/

Note:
The script can be tested in a virtual python environment :
- Installing aiosmtpd :
$ python3 -m venv /path/to/venv
$ source /path/to/venv/bin/activate
$ python setup.py install

- Eventually,  add symbolic link to ldap3 module or install it in to the venv
