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
import time
import os
import traceback
from email.mime.text import MIMEText
from email.header import decode_header
from email.header import make_header
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
            self.subject = self.confparser.get(self.module_name, 'subject', fallback='Auto reply: %s') # %s est rempalcé par le sujet du mail
            self.use_origin_msg_headers = self.confparser.getboolean(self.module_name, 'use_origin_msg_headers', fallback=True) # Delivered-to: et Received: du message d'orgine sont repris dans l'autoreply
            self.origin_msg_headers = self.confparser.get(self.module_name, 'origin_msg_headers', fallback='Delivered-to,Received').rstrip(',').split(',')
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
            #self.autoreply_from = self.confparser.get(self.module_name, 'from', fallback=None) # TODO LDAP / INFOSSOURCES ?

            # delais
            self.default_delay = self.confparser.getint(self.module_name, 'default_delay', fallback=720) # un autoreply toutes les "delay" minutes
            self.delay_path = self.confparser.get(self.module_name, 'delay_path', fallback='/var/cache/autoreply/')
            delay_path_mod = self.confparser.get(self.module_name, 'delay_path_mod', fallback='755')
            delay_path_owner = self.confparser.get(self.module_name, 'delay_path_owner', fallback=None)
            create_dir = self.confparser.getboolean(self.module_name, 'delay_createdir', fallback=True)
            self.delay_file_mod  = self.confparser.get(self.module_name, 'delay_file_mod', fallback='644')
            self.delay_file_owner = self.confparser.get(self.module_name, 'delay_file_owner', fallback=None)
            self.init_dir(self.delay_path, mod=delay_path_mod, owner=delay_path_owner, create_dir=create_dir)
            self.delay_file_format = self.confparser.get(self.module_name, 'delay_file_format', fallback='AutoReply..%u..%mf.txt') # %u = uid, %mf = mailfrom
            # TODO nettoyage des fichiers automatique ? Quand ?

            # Exceptions
            self.exceptions = {}
            mfe = self.confparser.get(self.module_name, 'mailfrom_exceptions', fallback='mailer-daemon@*,nobody@*,*-owner@*,www-data@*,robot-*@*,^@*').rstrip(',').split(',')
            self.exceptions['mailfrom_exceptions'] = [ re.sub('\*', '.*?', x) for x in mfe ]
            self.exceptions['no_reply_to_autoreply'] = self.confparser.getboolean(self.module_name, 'no_reply_to_autoreply', fallback=True)
            self.exceptions['no_reply_to_robot'] = self.confparser.getboolean(self.module_name, 'no_reply_to_robot', fallback=True)
            self.exceptions['no_reply_to_spam'] = self.confparser.getboolean(self.module_name, 'no_reply_to_spam', fallback=True)
            self.exceptions['no_reply_precedence'] = self.confparser.get(self.module_name, 'no_reply_precedence', fallback='bulk,list,junk').rstrip(',').split(',')
            nrh = self.confparser.get(self.module_name, 'no_reply_headers', fallback='list-*,X-list-*').rstrip(',').split(',')
            self.exceptions['no_reply_headers'] = [ re.sub('\*', '.*?', x) for x in nrh ]
            nrsh = self.confparser.get(self.module_name, 'no_reply_spam_headers',fallback='X-Spam-Flag:yes').rstrip(',').split(',')
            self.exceptions['no_reply_spam_headers'] = []
            for x in nrsh:
                self.exceptions['no_reply_spam_headers'].append(x.split(':'))

            # Lecture configuration des sources
            self.options.get_module('INFOSSOURCES').AUTOREPLY_init_confs()

            self.init_rules_rule_types()
            self.init_rules_re()


        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise

    ########################################
    def init_rules_rule_types(self):
       self. rule_types = { \
        'LDAP':self.play_rule_LDAP, \
        'JOKE':self.play_rule_JOKE, \
        'PCRE':self.play_rule_PCRE, \
        'RAIN':self.play_rule_RAIN, \
        'RAEX':self.play_rule_RAEX, \
        'ORIG':self.play_rule_ORIG \
        }

    ########################################
    def init_rules_re(self):
        self.re_rules = re.compile(r'^(\d+)~ ((%s):(.*?))(( DDEB:(\d{8}))?( DFIN:(\d{8}))?( DSVT:(\d?))?)?( FREQ:(\d*))?( TEXTE:(.*?)?)$'%('|'.join([x for x in self.rule_types])), re.DOTALL)
        # TODO texte directement dans l'entrée...
        # TODO DFIN:0/20170523 : désactive la date de fin ?!
        self.regrp = {
            'order':0,
            'type':2,
            'tparams':3,
            'ddebval':6,
            'dfinval':8,
            'dsvtval':10,
            'freqval':12,
            'textval':14 }

    ########################################
    def play_rule_LDAP(self, user_mail_from, rcptto, envelope, headers):
        self.log.warning('{} - LDAP is not impemented yet.'.format(self.module_name)) # TODO
        return False

    ########################################
    def play_rule_JOKE(self, user_mail_from, rcptto, envelope, headers):
        self.log.warning('{} - JOKE is not impemented yet.'.format(self.module_name)) # TODO
        return False

    ########################################
    def play_rule_PCRE(self, user_mail_from, rcptto, envelope, headers):
        self.log.warning('{} - PCRE is not impemented yet.'.format(self.module_name)) # TODO
        return False

    ########################################
    def play_rule_RAIN(self, user_mail_from, rcptto, envelope, headers):
        self.log.debug('{} - playing RAIN rule for sender {}.'.format(self.module_name, envelope.mail_from))
        return self.options.get_module('INFOSSOURCES').AUTOREPLY_RAIN_apply_rule_in_sources(envelope.mail_from)

    ########################################
    def play_rule_RAEX(self, user_mail_from, rcptto, envelope, headers):
        self.log.debug('{} - playing RAEX rule for sender {}.'.format(self.module_name, envelope.mail_from))
        return self.options.get_module('INFOSSOURCES').AUTOREPLY_RAEX_apply_rule_in_sources(envelope.mail_from)

    ########################################
    def play_rule_ORIG(self, user_mail_from, rcptto, envelope, headers):
        self.log.debug('{} - ORIG is not impemented yet.'.format(self.module_name)) # TODO
        return False

    ########################################
    def sort_rules_key(self, key):
        return key['order']

    ########################################
    def parse_rules(self, rawrules):
        try:
            rules = []
            for x in rawrules:
                r = self.re_rules.findall(x)
                if r:
                    rule = {}
                    rule['order'] = int(r[0][self.regrp['order']])
                    rule['type'] = r[0][self.regrp['type']]
                    if r[0][self.regrp['tparams']] != '': rule['tparams'] = r[0][self.regrp['tparams']]
                    if r[0][self.regrp['ddebval']] != '': rule['ddebval'] = r[0][self.regrp['ddebval']]
                    if r[0][self.regrp['dfinval']] != '': rule['dfinval'] = r[0][self.regrp['dfinval']]
                    if r[0][self.regrp['dsvtval']] != '': rule['dsvtval'] = r[0][self.regrp['dsvtval']]
                    if r[0][self.regrp['freqval']] != '': rule['freqval'] = int(r[0][self.regrp['freqval']])
                    if r[0][self.regrp['textval']] != '': rule['textval'] = r[0][self.regrp['textval']]
                    # TODO insérer trier dans rules.... bisect.insort_left ?
                    rules.append(rule)
            rules.sort(key=self.sort_rules_key)
            return rules
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise

    ########################################
    def is_check_freq_ok(self, delay, delay_file):
        try:
            now = time.time()
            if os.path.exists(delay_file):
                mtime = os.path.getmtime(delay_file)
                if mtime+delay*60 > now:
                    return False
            return True
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise

    ########################################
    def autroreply_send_mail(self, rule, user_mail_from, uid, envelope, headers):
        try:
            self.log.debug('{} - Sending mail for autoreply for {}'.format(self.module_name, uid))
            msg = MIMEText(rule['textval'], 'utf-8')

            # TODO insertion nouvelle ligne entête dans le message ?

            # Ajout des headers d'origine # TODO
            if self.use_origin_msg_headers:
                for x in headers:
                    if x in self.origin_msg_headers:
                        msg[x] = headers[x]

            # Ajout des headers nécessaire :
            if self.check_header('Subject', headers, envelope):
                msg['Subject'] = re.sub('%s', str(make_header(decode_header(headers['Subject']))), self.subject)
            msg['From'] = user_mail_from # TODO ajouter la décoration du cn ?
            if self.check_header('To', headers, envelope):
                msg['To'] = envelope.mail_from # TODO émetteur interne a décoré ou externe (reprendre le from du message)
            # if self.check_header('Message-ID', headers, envelope):
            #    for x in self.add_headers:
            #        msg[x] = re.sub('%mid', headers['Message-ID'], self.add_headers[x])
            self.options.get_module('SENDMAIL').send_mimetext_email(self.autoreply_mailfrom, envelope.mail_from, msg)
        except:
            print('{} - {}'.format(self.module_name, traceback.format_exception(*sys.exc_info()))) # TODO
            raise

    ########################################
    def apply_rules(self, rules, user_mail_from, rcptto, envelope, headers):
        try:
            self.log.debug('{} - Applying rules for autoreply for {}'.format(self.module_name, rcptto))
            today = time.strftime("%Y%m%d")
            delay_file = re.sub('%u', rcptto, self.delay_file_format)
            delay_file = re.sub('%mf', envelope.mail_from, delay_file)
            for rule in rules:
                self.log.debug('{} - for {} : rule {}'.format(self.module_name, rcptto, rule))
                if not 'textval' in rule:
                    self.log.debug('{} - texte is empty for {} : {}'.format(self.module_name, rcptto, rule)) # TODO
                    continue
                if not 'ddebval' in rule or rule['ddebval'] > today:
                    continue
                if not 'dfinval' in rule or rule['dfinval'] < today:
                    continue
                if 'dsvtval' in rule:
                    self.log.warning('{} - DSVT is not impemented yet.'.format(self.module_name)) # TODO
                if not self.is_check_freq_ok(self.default_delay if not 'freqval' in rule else rule['freqval'], '{}/{}'.format(self.delay_path, delay_file)):
                    self.log.info('{} - too close freq for {} : {}'.format(self.module_name, rcptto, rule)) # TODO
                    continue
                if not self.rule_types[rule['type']](user_mail_from, rcptto, envelope, headers):
                    self.log.debug('{} - For user {} the {} rule return False for {} ({})'.format(self.module_name, rcptto, rule['type'], envelope.mail_from, rule))
                    continue
                self.autroreply_send_mail(rule, user_mail_from, rcptto, envelope, headers)
                self.touch_file(delay_file, mod=self.delay_file_mod, owner=self.delay_file_owner, path=self.delay_path)
                break
        except:
            self.log.error('{} - {}'.format(self.module_name, traceback.format_exception(*sys.exc_info()))) # TODO
            raise

    ########################################
    def check_exception(self, envelope, headers):
        try:
            for x in self.exceptions['mailfrom_exceptions']:
                if re.search(x, envelope.mail_from):
                    self.log.info('{} - No response to sender {}'.format(self.module_name, envelope.mail_from)) # TODO ajouter message-id
                    return False
            if self.exceptions['no_reply_to_autoreply'] and 'Auto-submitted' in headers and headers['Auto-submitted'].lower() == 'no':
                self.log.info('{} - No response to Auto-submitted message from {}'.format(self.module_name, envelope.mail_from)) # TODO ajouter message-id
                return False
            if self.exceptions['no_reply_to_robot']:
                if 'Precedence' in headers and headers['Precedence'] not in self.exceptions['no_reply_precedence']:
                    self.log.info('{} - No response to robot message from {}'.format(self.module_name, envelope.mail_from)) # TODO ajouter message-id
                    return False
                for h in headers:
                    for x in self.exceptions['no_reply_headers']:
                        if re.search(x, h):
                            self.log.info('{} - No response to robot message {} with {} header'.format(self.module_name, envelope.mail_from, h)) # TODO ajouter message-id
                            return False
            if self.exceptions['no_reply_to_spam']:
                for x in self.exceptions['no_reply_spam_headers']:
                    if x[0] in headers and headers[x[0]] == x[1]:
                        return False
            return True
        except:
            self.log.error('{} - {}'.format(self.module_name, traceback.format_exception(*sys.exc_info()))) # TODO
            raise

    ########################################
    def run(self, envelope, headers):
        try:
            if self.check_exception(envelope, headers):
                for rcptto in envelope.rcpt_tos:
                    self.log.debug('{} - Search for autoreply rules for {}'.format(self.module_name, rcptto))
                    rawrules, user_mail_from = self.options.get_module('INFOSSOURCES').AUTOREPLY_search_user_info_in_sources(rcptto)
                    if rawrules and user_mail_from:
                        rules = self.parse_rules(rawrules)
                        self.apply_rules(rules, user_mail_from, rcptto, envelope, headers)
                    else:
                        if not user_mail_from:
                            self.log.error('{} - infossources have no mail emission for user {}'.format(self.module_name, rcptto))
        except:
            self.log.error('{} - {}'.format(self.module_name, traceback.format_exception(*sys.exc_info()))) # TODO
            raise
