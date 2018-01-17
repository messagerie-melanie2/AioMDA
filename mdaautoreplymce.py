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
import traceback
import time
import re
import os
from email.mime.text import MIMEText
from email.header import decode_header
from email.header import make_header
from mdaautoreply import MdaAutoReply
from Recurrence import Recurrence

################################################################################
class MdaAutoReplyMCE(MdaAutoReply):
    ########################################

    ########################################
    def init_rules_rule_types(self):
        self. rule_types = {
            'IN': self.play_rule_IN,
            'OUT': self.play_rule_OUT,
            'ALL': self.play_rule_ALL,
        }

    ########################################
    def init_rules_re(self):
        # ^[0-9]{2};{Version};(ALL|IN|OUT);[0-9]{14}Z;[0-9]{14}Z;[dhms][1-9][0-9]*;{repetitivite};[^;]*;[^;]*$
        # self.re_rules = re.compile(r'^(\d+)~ ((%s):(.*?))(( DDEB:(\d{8}))?( DFIN:(\d{8}))?( DSVT:(\d?))?)?( FREQ:(\d*))?( TEXTE:(.*?)?)$'%('|'.join([x for x in self.rule_types])), re.DOTALL)
        # TODO texte directement dans l'entrée...
        # TODO DFIN:0/20170523 : désactive la date de fin ?!
        self.regrp = {
            'order': 0,
            'version': 1,
            'type': 2,
            'ddebval': 3,
            'dfinval': 4,
            'freqval': 5,
            'repetitivite': 6,
            'subject': 7,
            'textval': 8}


    ########################################
    def play_rule_IN(self, user_mail_from, rcptto, envelope, headers):
        self.log.debug('{} - playing IN rule for sender {}.'.format(self.module_name, envelope.mail_from))
        return self.options.get_module('INFOSSOURCES').AUTOREPLY_RAIN_apply_rule_in_sources(envelope.mail_from)

    ########################################
    def play_rule_OUT(self, user_mail_from, rcptto, envelope, headers):
        self.log.debug('{} - playing OUT rule for sender {}.'.format(self.module_name, envelope.mail_from))
        return self.options.get_module('INFOSSOURCES').AUTOREPLY_RAEX_apply_rule_in_sources(envelope.mail_from)

    ########################################
    def play_rule_ALL(self, user_mail_from, rcptto, envelope, headers):
        self.log.debug('{} - playing ALL rule for sender {}.'.format(self.module_name, envelope.mail_from))
        return self.options.get_module('INFOSSOURCES').AUTOREPLY_RAEX_apply_rule_in_sources(envelope.mail_from)

    ########################################
    def parse_rules(self, rawrules):
        try:
            rules = []
            mul = {"d":86400,"h":3600,"m":60,"s":1}
            for x in rawrules:
                r = x.split(';')
                if r and len(r) == 9:
                    self.log.debug('{}'.format(r))
                    rule = {}
                    rule['order'] = int(r[self.regrp['order']])
                    rule['version'] = int(r[self.regrp['version']])
                    rule['type'] = r[self.regrp['type']]
                    if r[self.regrp['ddebval']] != '': rule['ddebval'] = r[self.regrp['ddebval']]
                    if r[self.regrp['dfinval']] != '': rule['dfinval'] = r[self.regrp['dfinval']]
                    if r[self.regrp['freqval']] != '':
                        res = re.findall(r'^([dhms])([1-9][0-9]*)$',r[self.regrp['freqval']])
                        if res:
                            rule['freqval'] = mul[res[0][0]]*res[0][1]
                    if r[self.regrp['subject']] != '': self.subject = r[self.regrp['subject']]
                    if r[self.regrp['textval']] != '': rule['textval'] = r[self.regrp['textval']]
                    # TODO insérer trier dans rules.... bisect.insort_left ?
                    simple = Recurrence(r[self.regrp['repetitivite']])
                    if simple.isMaintenant():
                        rules.append(rule)
            rules.sort(key=self.sort_rules_key)
            return rules
        except:
            print('{} - {}'.format(self.module_name, traceback.format_exception(*sys.exc_info()))) # TODO
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
                # TODO émetteur interne a décoré ou externe (reprendre le from du message)
                msg['To'] = envelope.mail_from
            # if self.check_header('Message-ID', headers, envelope):
            #     for x in self.add_headers:
            #         msg[x] = re.sub('%mid', headers['Message-ID'], self.add_headers[x])
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
    def is_check_freq_ok(self, delay, delay_file):
        try:
            now = time.time()
            if os.path.exists(delay_file):
                mtime = os.path.getmtime(delay_file)
                self.log.debug('mtime+delay*60 : {} > now : {}'.format(mtime + delay * 60, now))
                if mtime + delay * 60 > now:
                    return False
            return True
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise
