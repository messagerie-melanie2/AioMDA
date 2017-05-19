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
import smtplib
from email.mime.text import MIMEText
from mdamodules import MdaModule
from mdamodules import MdaErrorCode
from mdamodules import MdaError

################################################################################
class MdaSendMail(MdaModule):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            if not self.options.check_required_modules(['INFOSSOURCES'], formodule=module_name):
                raise MdaError(MdaErrorCode()['MDA_ERR_NOTLOADED'], 'Some required modules are not loaded')
            self.smtphost = self.confparser.get(self.module_name, 'smtphost', fallback='localhost')
            self.smtpport = self.confparser.getint(self.module_name, 'smtpport', fallback=25)
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise
        
    ########################################    
    def send_mimetext_email(self, mailfrom, rcpttos, subject, message, From=None, Tos=None):
        try:
            msg = MIMEText(message, 'utf-8')
            msg['Subject'] = subject
            # TODO Si From ou Tos = None + option conf => search ldap
            msg['From'] = From if From else mailfrom
            msg['To'] = ', '.join(Tos) if Tos else ', '.join(rcpttos)
            cs = smtplib.SMTP(host=self.smtphost, port=self.smtpport)
            cs.send_message(msg, from_addr=mailfrom, to_addrs=rcpttos)
            cs.quit()
        except:
            self.log.error('{} - Error during sending email {}'.format(self.module_name, sys.exc_info()[0]))
