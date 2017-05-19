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
from mdamodules import MdaModule
from mdamodules import MdaErrorCode
from mdamodules import MdaError

################################################################################
class MdaAutoReply(MdaModule):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            if not self.options.check_required_modules(['INFOSSOURCES', 'SENDMAIL'], formodule=module_name):
                raise MdaError(MdaErrorCode()['MDA_ERR_NOTLOADED'], 'Some required modules are not loaded')
            # Message
            self.confparser.get(self.module_name, 'subject', fallback='Auto reply: %s') # %s est rempalcé par le sujet du mail
            self.confparser.getboolean(self.module_name, 'use_origin_msg_header', fallback=True) # Delivered-to: et Received: du message d'orgine sont repris dans l'autoreply
            self.add_headers = {}
            self.add_headers['Auto-submitted'] = self.confparser.get(self.module_name, 'Auto-submitted', fallback='Auto-Replied')
            self.add_headers['Precedence'] = self.confparser.get(self.module_name, 'Precedence', fallback='bulk')
            self.add_headers['In-Reply-To'] = self.confparser.get(self.module_name, 'In-Reply-To', fallback='%mid') # %mid = messageId
            self.add_headers['In-Reply-To'] = self.confparser.get(self.module_name, 'References', fallback='%mid') # %mid = messageId
            add_headers_list = self.confparser.get(self.module_name, 'add_headers', fallback=None)
            if add_headers_list:
                for x in add_headers_list.rstrip(',').split(','):
                    self.add_headers[x] = self.confparser.get(self.module_name, x)
            
            self.autoreply_mailfrom = self.confparser.get(self.module_name, 'mailfrom', fallback='<>')
            self.autoreply_mailfrom = self.confparser.get(self.module_name, 'from', fallback=None) # TODO LDAP / INFOSSOURCES ?
            
            # delais
            self.confparser.getint(self.module_name, 'delay', fallback=720) # un autoreply toutes les "delay" minutes
            self.delay_path = self.confparser.get(self.module_name, 'delay_path', fallback='/var/cache/autoreply/')
            delay_path_mod = self.confparser.get(self.module_name, 'delay_path_mod', fallback='755')
            delay_path_owner = self.confparser.get(self.module_name, 'delay_path_owner', fallback=None)
            create_dir = self.confparser.getboolean(self.module_name, 'delay_createdir', fallback=True)
            self.init_dir(self.delay_path, mod=delay_path_mod, owner=delay_path_owner, create_dir=create_dir)
            self.delay_file_format = self.confparser.get(self.module_name, 'delay_file_format', fallback='AutoReply..%u..%mf.txt') # %u = uid, %mf = mailfrom
            # TODO nettoyage des fichiers automatique ? Quand ?
            
            # Exceptions
            self.confparser.get(self.module_name, 'mailfrom_exceptions', fallback='mailer-daemon@*,nobody@*')
            self.confparser.getboolean(self.module_name, 'no_reply_to_autoreply', fallback=True)
            self.confparser.getboolean(self.module_name, 'no_reply_to_robot', fallback=True)
            self.confparser.getboolean(self.module_name, 'no_reply_to_spam', fallback=True)
            
            # Lecture configuration des sources
            self.options.get_module('INFOSSOURCES').AUTOREPLY_init_confs()

            type_word = ['AMED', 'MELA', 'AMEX', 'LDAP', 'JOKE', 'PCRE', 'RAIN', 'RAEX', 'ORIG'] # TODO Mettre 'AMED', 'MELA', 'AMEX' dans une classe AutoReplyM2
            self.re_rule = re.compile(r'^(\d*)~ ({}):.*?$'.format('|'.join(type_word)), re.DOTALL)
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise

    ########################################
    def parse_rules(self, rules):
        pass # TODO

    ########################################
    def run(self, envelope, headers):
        try:
            for rcptto in envelope.rcpt_tos:
                rawrules = self.options.get_module('INFOSSOURCES').AUTOREPLY_search_rules_in_sources(rcptto)
                if rawrules:
                    rules = self.parse_rules(rawrules)
                # TODO
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise
