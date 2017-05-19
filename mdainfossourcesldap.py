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
import ldap3
from ldap3.utils import uri as ldapuri
from mdamodules import MdaError
from mdamodules import MdaErrorCode
from mdainfossourcesgeneric import MdaInfosSourcesGeneric

################################################################################    
class MdaLdapRequestParams(object):
    ########################################
    def __init__(self, filter, base, scope='sub', deref='never', attrs=[ldap3.ALL_ATTRIBUTES], attrs_mapped=[ldap3.ALL_ATTRIBUTES], size_limit=0, time_limit=0, module_options=None):
        self.filter = filter
        self.base = base
        self.scope = self.get_ldap3_scope(scope)
        self.deref = self.get_ldap3_deref(deref)
        self.attrs = attrs
        self.attrs_mapped = attrs_mapped
        self.size_limit = size_limit
        self.time_limit = time_limit
        self.module_options = module_options
        
    ########################################
    def __getitem__(self, key):
        if key in self.module_options:
            return self.module_options[key]
        else:
            return None
            
    ########################################
    def __setitem__(self, key, value):
        if not self.module_options:
            self.module_options = {}
        self.module_options[key] = value
        
    ########################################
    def get_ldap3_scope(self,  configscope):
        confscope = configscope.lower()
        if confscope == 'sub':
            scope = ldap3.SUBTREE
        elif confscope == 'one'or scope == 'level':
            scope = ldap3.LEVEL
        elif confscope == 'base':
            scope = ldap3.BASE
        else:
            scope = ldap3.SUBTREE
        return scope

    ########################################
    def get_ldap3_deref(self,  configderef):
        confderef = configderef.lower()
        if confderef == 'never':
            deref = ldap3.DEREF_NEVER
        elif confderef == 'search':
            deref = ldap3.DEREF_SEARCH
        elif confderef == 'base':
            deref = ldap3.DEREF_BASE
        elif confderef == 'always':
            deref = ldap3.DEREF_ALWAYS
        else:
            deref = ldap3.DEREF_NEVER
        return deref

################################################################################    
class MdaInfosSourcesLDAP(MdaInfosSourcesGeneric):
    ########################################
    def __init__(self, module_name, options, confparser):
        super().__init__(module_name, options, confparser)
        try:
            self.attrs_by_substitute = {'%m':'mail', '%u':'uid'}
            # LDAP Uri
            self.uri = self.confparser.get(self.module_name, 'uri')
            self.uri_components = ldapuri.parse_uri(self.uri) 
            
            # TODO gérer un pool de connexion ?
            
            # TODO connexion authentifié
            self.requests_by_modules = {}            
            
            # attrs mapping
            self.attrs_list = self.confparser.get(self.module_name, 'attrs_list',  fallback='uid mail host autoreply').rstrip(' ').split(' ')
            self.attrs_map = {}
            for x in self.attrs_list:
                self.attrs_map[x] = self.confparser.get(self.module_name, x, fallback=x)
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise

    ########################################
    def check_attrs_list(self, attrs, all_attrs=None):
        if not all_attrs:
            all_attrs = self.attrs_list
        must_raise = False
        for x in attrs:
            if x  not in all_attrs:
                must_raise = True
                msg = '{} is not the list of attrs:{}'.format(x, all_attrs)
                self.log.error(msg)
        if must_raise:        
            raise MdaError(MdaErrorCode()['MDA_ERR_CONFIGURED'], msg)

    ########################################
    def ldap_connect_and_bind(self):
        try:
            server = ldap3.Server(self.uri_components['host'],  port=self.uri_components['port'],  use_ssl=self.uri_components['ssl'])
            conn = ldap3.Connection(server)
            if not conn.bind():
                self.log.error('{} - ldap error during bind: {}'.format(conn.result))
                raise MdaError(450, 'Configuration error') # TODO
            return conn
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise

    ########################################
    def filter_substitution(self, rawfilter, values_by_attrs):
        filter = None
        try:
            for x in self.attrs_by_substitute:
                if self.attrs_by_substitute[x] in values_by_attrs:
                    filter = re.sub(x, values_by_attrs[self.attrs_by_substitute[x]], rawfilter)
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise
        return filter

    ########################################
    def module_init_conf(self, module_name, filter_fallback='(objectClass=*)'):
        try:
            filter = self.confparser.get(self.module_name, '{}_filter'.format(module_name),  fallback=filter_fallback)
            base = self.confparser.get(self.module_name, '{}_base'.format(module_name)) # TODO fallback=None ?
            attrs = self.confparser.get(self.module_name, '{}_attrs'.format(module_name),  fallback=self.attrs_list).rstrip(' ').split(' ')
            self.check_attrs_list(attrs)
            attrs_mapped = [self.attrs_map[x] for x in attrs]
            scope = self.confparser.get(self.module_name, '{}_scope'.format(module_name),  fallback='sub')
            deref = self.confparser.get(self.module_name, '{}_deref'.format(module_name),  fallback='never')
            time_limit = self.confparser.getint(self.module_name, '{}_time_limit'.format(module_name), fallback=10)
            size_limit = self.confparser.getint(self.module_name, '{}_size_limit'.format(module_name), fallback=10)
            
            self.requests_by_modules[module_name] = MdaLdapRequestParams( \
                filter, \
                base, \
                scope=scope, \
                deref=deref, \
                attrs=attrs, \
                attrs_mapped=attrs_mapped, \
                size_limit=size_limit, \
                time_limit=time_limit)
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise
    
    ########################################
    def CHKRCPTTO_init_conf(self):
        try:
            self.module_init_conf('CHKRCPTTO', filter_fallback='(mail=%m)')
            self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_check_infos'] = self.confparser.getboolean(self.module_name, 'CHKRCPTTO_check_infos', fallback=True)
            self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_case_sensitive_check'] = self.confparser.getboolean(self.module_name, 'CHKRCPTTO_case_sensitive_check', fallback=False)
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise

    ########################################
    def CHKRCPTTO_checking_infos(self, rcptto, ldap_entry):
        try:
            f = self.options['fqdn'] if self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_case_sensitive_check'] else self.options['fqdn'].lower()
            for x in ldap_entry['attributes'][self.attrs_map['host']]:
                    h = x if self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_case_sensitive_check'] else x.lower()
                    if h == f:
                        return True
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
        return False

    ########################################
    def CHKRCPTTO_find_local_user(self, rcptto):
        localuser = None
        try:
            conn = self.ldap_connect_and_bind()
            filter = self.filter_substitution(self.requests_by_modules['CHKRCPTTO'].filter, {'mail':rcptto})
            conn.search( \
                search_base=self.requests_by_modules['CHKRCPTTO'].base, \
                search_filter=filter, \
                search_scope=self.requests_by_modules['CHKRCPTTO'].scope, \
                dereference_aliases=self.requests_by_modules['CHKRCPTTO'].deref, \
                attributes=self.requests_by_modules['CHKRCPTTO'].attrs_mapped)
            len_response = len(conn.response)
            if len_response == 1:
                if self.requests_by_modules['CHKRCPTTO']['CHKRCPTTO_check_infos']:
                    if self.CHKRCPTTO_checking_infos(rcptto, conn.response[0]):
                        localuser = conn.response[0]['attributes'][self.attrs_map['uid']][0]
                else:
                    localuser = conn.response[0]['attributes'][self.attrs_map['uid']][0]
            elif len_response > 1:
                self.log.error('{} - ldap request give more than one response for mail {}'.format(self.module_name, rcptto))
                raise MdaError(450, 'Configuration error') # TODO
            conn.unbind()
       # except ldap3.LDAPExceptionError as err:
        #    self.log.error(err)
        #    raise
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise
        return localuser

    ########################################
    def AUTOREPLY_init_conf(self, filter_fallback='(uid=%u)'):
        try:
            self.module_init_conf('AUTOREPLY')
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise
    
    ########################################
    def AUTOREPLY_search_rules(self, rcptto):
        '''
        note : à ce momment là rcptto doit avoir la valeur de uid
        '''
        rules = None
        try:
            conn = self.ldap_connect_and_bind()
            filter = self.filter_substitution(self.requests_by_modules['AUTOREPLY'].filter, {'uid':rcptto})
            conn.search( \
                search_base=self.requests_by_modules['AUTOREPLY'].base, \
                search_filter=filter, \
                search_scope=self.requests_by_modules['AUTOREPLY'].scope, \
                dereference_aliases=self.requests_by_modules['AUTOREPLY'].deref, \
                attributes=self.requests_by_modules['AUTOREPLY'].attrs_mapped)
            len_response = len(conn.response)
            if len_response == 1:
                if self.attrs_map['autoreply'] in conn.response[0]['attributes']:
                    rules = conn.response[0]['attributes'][self.attrs_map['autoreply']]
            elif len_response > 1:
                self.log.error('{} - ldap request give more than one response for mail {}'.format(self.module_name, rcptto))
                raise MdaError(450, 'Configuration error') # TODO
            conn.unbind()
        except:
            self.log.error('{} - {}'.format(self.module_name, sys.exc_info()[0]))
            raise
        return rules
        
