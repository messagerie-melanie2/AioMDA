#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Ce fichier est développé pour réaliser un MDA (Mail Delivery Agent)
réalisant diverses fonctions annexes

AioMda Copyright © 2017  PNE Annuaire et Messagerie/MEDDE

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import logging
import sys
import os
import shutil

################################################################################
class MdaErrorCode(object):
    ########################################
    def __init__(self):
        self.errorcodes = { \
            'MDA_SUCCESS':0, \
            'MDA_ERR_GENERIC':1, \
            'MDA_ERR_ARGS':2, \
            'MDA_ERR_UNIMPLEMENTED':3, \
            'MDA_ERR_NOTLOADED':4, \
            'MDA_ERR_CONFIGURED':5, 
            'MDA_ERR_ASYNCIO':6, \
            'MDA_ERR_PERM':7, \
            'MDA_ERR_FILE':8, \
            'MDA_ERR_SENDMAIL':8 }
            
    ########################################
    def __getitem__(self, code):
        return self.errorcodes[code]
        
    ########################################
    def get_errname_with_errnumber(self, errnumber):
        return list(self.errorcodes)[list(self.errorcodes.values()).index(errnumber)] # TODO try/except ?


################################################################################
class MdaError(Exception):
    ########################################
    def __init__(self, value, strval):
        self.err = value
        self.strerror = strval


################################################################################
class MdaOptions(object):
    ########################################
    def __init__(self, all_modules):
        self.log = logging.getLogger('AioMda')
        self.all_modules = all_modules
        self.modules = {}
        self.options = {}
        
    ########################################
    def __getitem__(self, key):
        if key in self.options:
            return self.options[key]
        else:
            return None
            
    ########################################
    def __setitem__(self, key, value):
        self.options[key] = value
    
    ########################################
    def set_module(self,module_name, module):
        if module_name not in self.all_modules:
            msg = '{} is not the list of avaiables modules:{}'.format(module_name, self.all_modules)
            self.log.error(msg)
            raise MdaError(MdaErrorCode()['MDA_ERR_NOTLOADED'], msg)
        else:
            self.modules[module_name] = module
        
    ########################################
    def get_module(self, module_name):
        if module_name in self.modules:
            return self.modules[module_name]
        else:
            return None
            
    ########################################
    def is_module_active(self, module_name):
        if module_name in self.modules:
           return True
        else:
            return False

    ########################################
    def check_modules_list(self, modlist, all_modules=None):
        if not all_modules:
            all_modules = self.all_modules
        must_raise = False
        for x in modlist:
            if x  not in all_modules:
                must_raise = True
                msg = '{} is not the list of avaiables modules:{}'.format(x, all_modules)
                self.log.error(msg)
        if must_raise:        
            raise MdaError(MdaErrorCode()['MDA_ERR_CONFIGURED'], msg)
            
    ########################################
    def check_required_modules(self, needed, formodule=None):
        ret = True
        for x in needed:
            if not self.is_module_active(x):
                ret = False
                self.log.error('{} need to be active{}'.format(x, '' if formodule == None else ' {}'.format(formodule)))
        return ret
                

################################################################################
class MdaModule(object):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            self.log = logging.getLogger('AioMda')
            self.module_name = module_name
            self.confparser = confparser
            self.options = options
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise
        
    ########################################    
    def run(self):
        pass

    ########################################
    def create_dir(self, path, mod='755', owner=None):
        try:
            omod = int(mod, 8)
            os.makedirs(path, omod)
            if owner:
                ugid = owner.split(':')
                shutil.chown(path, user=ugid[0], group=ugid[1] if len(ugid) == 2 else None )
        except:
            self.log.error('{} - erreur during create_dir {} : {}'.format(self.module_name, path, sys.exc_info()[0]))
            raise
                
    ########################################
    def init_dir(self, path, mod='755', owner=None, create_dir=True):
        if os.path.exists(path):
            if not os.path.isdir(path):
                msg = '{} - {} exists and is not a directory.'.format(self.module_name, self.notify_path)
                self.log.error(msg)
                raise MdaError(MdaErrorCode()['MDA_ERR_FILE'],  msg)
        else:
            if create_dir:
                self.create_dir(path, mod=mod, owner=owner)

    ########################################
    def touch_file(self, file, path=None, mod=None, owner=None):
        try:
            if not path:
                p = os.path.dirname(file)
                f = os.path.basename(file)
                fp = file
            else:
                p = path
                f = file
                fp = '{}/{}'.format(p, f)
            if os.path.exists(fp):
                os.utime(fp)
            else:
                os.mknod(fp)
                if mod:
                    os.chmod(fp, int(mod, 8))
                if owner:
                    ugid = owner.split(':')
                    shutil.chown(fp, user=ugid[0], group=ugid[1] if len(ugid) == 2 else None)
        except OSError as e:
            self.log.error('{} - cannot create file {} : {}'.format(self.module_name, fp, e))
            raise
        except:
            self.log.error('{} - erreur during create_dir {} : {}'.format(self.module_name, path, sys.exc_info()[0]))
            raise
            

    ########################################
    def check_header(self, value, headers, envelope):
        if value in headers:
            return True
        else:
            errmsg = 'message from {} to {} has no {}'.format(envelope.mail_from, ','.join(envelope.rcpt_tos), value)
            self.log.error('{} - {}'.format(self.module_name, errmsg))
            raise MdaError(MdaErrorCode()['MDA_ERR_SENDMAIL'], 'AutoReply cannot be sent : {}'.format(errmsg))
