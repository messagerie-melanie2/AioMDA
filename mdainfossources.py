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
from mdamodules import MdaModule
from mdamodules import MdaErrorCode
from mdamodules import MdaError
from mdainfossourcesgeneric import MdaInfosSourcesGeneric
from mdainfossourcesgeneric import MdaInfosSourcesTEXT
from mdainfossourcesldap import MdaInfosSourcesLDAP
from mdainfossourcesldapm2 import MdaInfosSourcesLDAPM2

################################################################################
class MdaInfosSources(MdaModule):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            self.actives_sources = self.confparser.get(module_name, 'sources', fallback='LDAP').upper().rstrip(',').split(',')

            # TODO possibilté de plusieurs sources de chaque type (par exemple plusieurs sources ldap pointant sur des serveurs ldap différents
            # TODO possibilité de différentes sources en fonction des modules
            
            self.sources_dict = {}
            for x in self.actives_sources:
                self.log.debug('MdaInfosSources: loading {}'.format(x))
                if x == 'LDAP':
                    self.sources_dict['LDAP'] = MdaInfosSourcesLDAP('INFOSSOURCESLDAP', self.options, confparser)
                elif x == 'LDAPM2':
                    self.sources_dict['LDAPM2'] = MdaInfosSourcesLDAPM2('INFOSSOURCESLDAPM2', self.options, confparser)
                elif x == 'TEXT':
                    self.sources_dict['TEXT'] = MdaInfosSourcesTEXT('INFOSSOURCESTEXT', self.options, confparser)
                elif x == 'GENERIC':
                    self.sources_dict['GENERIC'] = MdaInfosSourcesGeneric('INFOSSOURCESGENERIC', self.options, confparser)
                else:
                    msg = '{} is not a module of {}'.format(x, self.module_name)
                    print(msg)
                    raise MdaError(MdaErrorCode()['MDA_ERR_CONFIGURED'], msg)
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise

    ########################################
    def CHKRCPTTO_init_confs(self):
        for x in self.actives_sources:
            self.sources_dict[x].CHKRCPTTO_init_conf()

    ########################################
    def CHKRCPTTO_find_local_user_in_sources(self, rcptto):
        for x in self.actives_sources:
            localuser = self.sources_dict[x].CHKRCPTTO_find_local_user(rcptto)
            if localuser:
                return localuser
        return None
        
    ########################################
    def AUTOREPLY_init_confs(self):
        for x in self.actives_sources:
            self.sources_dict[x].AUTOREPLY_init_conf()
            
    ########################################
    def AUTOREPLY_search_user_info_in_sources(self, rcptto):
        rules = None
        user_mail_from = None
        for x in self.actives_sources:
            rules, user_mail_from = self.sources_dict[x].AUTOREPLY_search_user_info(rcptto)
            if rules:
                break
        return (rules, user_mail_from)

    ########################################
    def AUTOREPLY_RAIN_apply_rule_in_sources(self, mail):
        for x in self.actives_sources:
            ret = self.sources_dict[x].AUTOREPLY_RAIN_apply_rule(mail)
            if ret:
                return ret
    
    ########################################
    def AUTOREPLY_RAEX_apply_rule_in_sources(self, mail):
        for x in self.actives_sources:
            ret = self.sources_dict[x].AUTOREPLY_RAEX_apply_rule(mail)
            if ret:
                return ret
    
    
