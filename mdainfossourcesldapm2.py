#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Ce fichier est développé pour réalisé un MDA (Mail Delivery Agent)
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
#import ldap3
#from ldap3.utils import uri as ldapuri
from mdainfossourcesldap import MdaInfosSourcesLDAP

################################################################################    
class MdaInfosSourcesLDAPM2(MdaInfosSourcesLDAP):
    ########################################
    def CHKRCPTTO_checking_infos(self, rcptto, ldap_entry):
        try:
            f = self.options['fqdn'] if self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_case_sensitive_check'] else self.options['fqdn'].lower()            
            mails = ldap_entry['attributes'][self.attrs_map['mail']] if self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_case_sensitive_check'] else [x.lower() for x in ldap_entry['attributes'][self.attrs_map['mail']]]
            for x in ldap_entry['attributes'][self.attrs_map['host']]:
                mmr = re.match(r'^(.*?)@(.*?)$', x)
                if mmr:
                    mail = re.sub('%',  '@', mmr.group(1))
                    server = mmr.group(2) if self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_case_sensitive_check'] else mmr.group(2).lower()
                    if mail in mails and server == f:
                        return ldap_entry['attributes'][self.attrs_map['uid']][0]
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise
        return False

