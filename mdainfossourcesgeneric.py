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

import sys
import re
from mdamodules import MdaModule
#from mdamodules import MdaError

################################################################################
class MdaInfosSourcesGeneric(MdaModule):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            self.re_rcptto = re.compile(r'(.*?)@(.*?)')
        except:
            self.log.error(sys.exc_info()[0])
            raise
    
    ########################################
    def CHKRCPTTO_init_conf(self):
        pass
    
    ########################################
    def CHKRCPTTO_find_local_user(self,  rcptto):
        try:
            dest = self.re_rcptto.match(rcptto)
            if dest:
                local = dest.group(1)
                self.log.debug('{} - rcptto {} -> {}'.format(self.module_name, rcptto, local))
                return local
        except:
            self.log.error(sys.exc_info()[0])
        return None # TODO option pour renvoyer l'utilisateur toujours ou None

    ########################################
    def AUTOREPLY_init_conf(self):
        pass

    ########################################
    def AUTOREPLY_search_rules(self, rcptto):
        pass
        
    ########################################
    def AUTOREPLY_RAIN_apply_rule(self, mail):
        pass
    
    ########################################
    def AUTOREPLY_RAEX_apply_rule(self, mail):
        pass


################################################################################
# Only for testing purpose for CHKRCPTTO_find_local_user
class MdaInfosSourcesTEXT(MdaInfosSourcesGeneric):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            path = confparser.get(module_name, 'path')
            file = open(path,  'r')
            self.users = file.read().splitlines()
        except:
            self.log.error(sys.exc_info()[0])
            raise

    ########################################
    def CHKRCPTTO_find_local_user(self,  rcptto):
        try:
            local = super().CHKRCPTTO_find_local_user(rcptto)
            if local and local in self.users:
                self.log.debug('{} - rcptto {} -> {}'.format(self.module_name, rcptto, local))
                return local
        except:
            self.log.error(sys.exc_info()[0])
        return None


################################################################################    
class MdaInfosSourcesSQL(MdaInfosSourcesGeneric):
    pass # TODO

################################################################################    
class MdaInfosSourcesPGSQL(MdaInfosSourcesSQL):
    pass # TODO
    
################################################################################    
class MdaInfosSourcesMYSQL(MdaInfosSourcesSQL):
    pass # TODO
