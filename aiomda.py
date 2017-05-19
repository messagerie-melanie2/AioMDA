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

import argparse
import configparser
import sys
import re
import socket
import logging
from logging.handlers import SysLogHandler
from email.parser import BytesParser
import asyncio
# aiosmtpd
from aiosmtpd.controller import Controller
from aiosmtpd.lmtp import LMTP as LMTPServer
from aiosmtpd.handlers import Proxy
# Modules
from mdamodules import MdaOptions
from mdamodules import MdaErrorCode
from mdamodules import MdaError
from mdainfossources import MdaInfosSources
from mdachkrcptto import MdaChkRcptto
from mdasendmail import MdaSendMail
from mdanotifyzp import MdaNotifyZp
from mdaautoreply import MdaAutoReply

################################################################################
class AioMdaServer(LMTPServer):
    ########################################
    def __init__(self, handler, options, enable_SMTPUTF8=False, decode_data=False, hostname=None, tls_context=None, require_starttls=False, loop=None):
        self.log = logging.getLogger('AioMda')
        self.options = options
        self.re_rcptto = re.compile(r'TO:<(.*?)>')
        super().__init__(handler, enable_SMTPUTF8=enable_SMTPUTF8,  decode_data=decode_data, hostname=hostname, tls_context=tls_context, require_starttls=require_starttls, loop=loop)

    ########################################
    # TODO le programme raise si le serveur lmtp final n'est pas démarré
    def smtp_RCPT(self, arg):
        dest = self.re_rcptto.match(arg)
        if dest:
            rcptto = dest.group(1)
            try:
                localuser = self.options.get_module('CHKRCPTTO').run(rcptto)
                if localuser:
                    self.log.info('AioMdaServer.smtp_RCPT: {} -> {}'.format(arg, localuser))
                    if self.options.is_module_active('NOTIFYZP'):
                        self.options.get_module('NOTIFYZP').run(localuser)
                    yield from super().smtp_RCPT('TO:<{}>'.format(localuser))
                else:
                    self.log.warning('AioMdaServer.smtp_RCPT: No such user {}'.format(arg))
                    yield from self.push('550 No such user {} here'.format(arg))
            except:
                self.log.error('Error during smtp_RCPT: {}'.format(sys.exc_info()[0]))
                yield from self.push('450 Configuration error'.format(arg))
        else:
            self.log.error('Error re smtp_RCPT') # TODO meilleur message
            yield from self.push('450 Configuration error'.format(arg))

#    ########################################
#    def smtp_LHLO(self, arg):
#        print('smtp_LHLO: {}'.format(arg))
#        yield from super().smtp_LHLO(arg)
#
#    ########################################
#    def smtp_NOOP(self, arg):
#        print('smtp_NOOP: {}'.format(arg))
#        yield from super().smtp_NOOP(arg)
#
#    ########################################
#    def smtp_QUIT(self, arg):
#        print('smtp_QUIT: {}'.format(arg))
#        yield from super().smtp_QUIT(arg)
#
#    ########################################
#    def smtp_VRFY(self, arg):
#        print('smtp_VRFY: {}'.format(arg))
#        yield from super().smtp_VRFY(arg)
#
#    ########################################
#    def smtp_MAIL(self, arg):
#        print('smtp_MAIL: {}'.format(arg))
#        yield from super().smtp_MAIL(arg)
#
#    ########################################
#    def smtp_RSET(self, arg):
#        print('smtp_RSET: {}'.format(arg))
#        yield from super().smtp_RSET(arg)
#
#    ########################################
#    def smtp_DATA(self, arg):
#        print('smtp_DATA: {}'.format(arg))
#        print('smtp_DATA, from: {}'.format(self.envelope.mail_from))
#        print('smtp_DATA, rcpttos: {}'.format(self.envelope.rcpt_tos))
#        yield from super().smtp_DATA(arg)


################################################################################
class AioMdaController(Controller):
    ########################################
    def __init__(self, handler, options, loop=None, hostname=None, port=8025, *,
            ready_timeout=1.0, enable_SMTPUTF8=True):
            self.log = logging.getLogger('AioMda')
            self.options = options
            super().__init__(handler, loop=loop, hostname=hostname, port=port, ready_timeout=ready_timeout, enable_SMTPUTF8=enable_SMTPUTF8)
    
    ########################################
    def factory(self):
        return AioMdaServer(self.handler,  self.options)
        

################################################################################
class AioMdaProxy(Proxy):
    ########################################
    def __init__(self, options, remote_hostname, remote_port):
        self.log = logging.getLogger('AioMda')
        self.options = options
        super().__init__(remote_hostname, remote_port)

#    ########################################
#    @asyncio.coroutine
#    def handle_MAIL(self, server, session, envelope, address, mail_options):
#        print('handle_MAIL:\naddress: {}\nenvelope.mail_from: {}\nenvelope.content: {}'.format(address,  envelope.mail_from, envelope.content))
#        envelope.mail_from = 'vachement.bien'
#        return '250 OK'
#
#    ########################################
#    @asyncio.coroutine
#    def handle_RCPT(self, server, session, envelope, address, rcpt_options):
#        print('handle_RCPT:\naddress: {}\nenvelope.mail_from: {}\nenvelope.content: {}'.format(address,  envelope.mail_from, envelope.content))
#        envelope.rcpt_tos = ['titi',  'tutu']
#        return '250 OK'
#    
#    ########################################
#    @asyncio.coroutine
#    def handle_DATA(self, server,  session, envelope):
#        return '250 OK'

################################################################################
class AioMda(object):
    ########################################
    def __init__(self, configfile):
        try:
            self.options = MdaOptions(['INFOSSOURCES', 'CHKRCPTTO', 'SENDMAIL', 'NOTIFYZP'])
            self.confparser = configparser.ConfigParser(interpolation=None)
            self.confparser.read(configfile)
            # DEFAULT
            self.options['debug'] = self.confparser.getboolean('DEFAULT', 'debug', fallback=False)
            self.options['fqdn'] = self.confparser.get('DEFAULT', 'fqdn',  fallback=None)
            if not self.options['fqdn']:
                self.options['fqdn'] = socket.getfqdn()
            modlist = self.confparser.get('DEFAULT', 'modules', fallback='').upper().rstrip(',').split(',')
            self.options.check_modules_list(modlist)
            
            # TODO configparser pour log
            self.log = logging.getLogger('AioMda')
            self.log.setLevel(logging.DEBUG if self.options['debug'] else logging.INFO)
            handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_MAIL)
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s') # TODO
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
            
            # INPUT
            self.listen_host = self.confparser.get('INPUT', 'listen_host', fallback='localhost')
            self.listen_port = self.confparser.getint('INPUT', 'listen_port', fallback=100025)
            # OUTPUT
            self.dest_host = self.confparser.get('OUTPUT', 'dest_host', fallback='localhost')
            self.dest_port = self.confparser.getint('OUTPUT', 'dest_port', fallback=100026)
            # Modules obligatoires
            self.options.set_module('INFOSSOURCES', MdaInfosSources('INFOSSOURCES', self.options, self.confparser))
            self.options.set_module('CHKRCPTTO', MdaChkRcptto('CHKRCPTTO', self.options, self.confparser))
            # Modules optionnels
            if 'SENDMAIL' in modlist:
                self.options.set_module('SENDMAIL', MdaSendMail('SENDMAIL',self.options, self.confparser))
            if 'NOTIFYZP' in modlist:
                self.options.set_module('NOTIFYZP', MdaNotifyZp('NOTIFYZP',self.options, self.confparser))
            # Autres modules : TODO

            # Instention du Controlleur 
            self.controller = AioMdaController(AioMdaProxy(self.options, self.dest_host, self.dest_port), self.options,  hostname=self.listen_host, port=self.listen_port)
        except:
            print('{}'.format(sys.exc_info()[0])) # TODO
            if self.options and self.options['debug']:
                raise
            else:
                sys.exit(MdaErrorCode()['MDA_ERR_CONFIGURED'])

    ########################################
    def __del__(self):
        if 'controller' in self.__dict__ and self.controller:
            self.controller.stop()
    
    ########################################
    # en Python 3.5 : async def proxy_lmtp(self, loop):
    # en Python 3.4 : 
    @asyncio.coroutine
    def proxy_lmtp(self, loop):
        #self.controller = AioMdaController(Proxy(self.dest_host, self.dest_port), hostname=self.listen_host, port=self.listen_port)
        self.controller.start()

    ########################################
    def run(self):
        self.log.debug('{}:{} to {}:{}'.format(self.listen_host, self.listen_port, self.dest_host, self.dest_port))
        try:
            #logging.basicConfig(level=logging.DEBUG)
            loop = asyncio.get_event_loop()
            loop.create_task(self.proxy_lmtp(loop))
            loop.run_forever()
        except:
            self.log.error('{}'.format(sys.exc_info()[0])) # TODO
            sys.exit(MdaErrorCode()['MDA_ERR_ASYNCIO'])


################################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Modular MDA for postifx")
    parser.add_argument('configfile', help='path to configuration file')
    args = parser.parse_args()
    mmda = AioMda(args.configfile)
    mmda.run()
