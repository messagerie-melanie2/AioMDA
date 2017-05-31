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

#import sys
#import re
#from mdamodules import MdaErrorCode
#from mdamodules import MdaError
from mdautoreply import MdaAutoReply

################################################################################
class MdaAutoReply(MdaAutoReply):
    ########################################
    def init_rules_rule_types(self):
        super().init_rules_rule_types()
        self. rule_types['AMED'] = self.play_rule_AMED
        self. rule_types['MELA'] = self.play_rule_MELA
        self. rule_types['AMEX'] = self.play_rule_AMEX
    
    ########################################
    def play_rule_AMED(self, user_mail_from, rcptto, envelope, headers):
        self.log.warning('{} - AMED is not impemented yet.'.format(self.module_name)) # TODO
        return False
    
    ########################################
    def play_rule_MELA(self, user_mail_from, rcptto, envelope, headers):
        self.log.warning('{} - MELA is not impemented yet.'.format(self.module_name)) # TODO
        return False
    
    ########################################
    def play_rule_AMEX(self, user_mail_from, rcptto, envelope, headers):
        self.log.warning('{} - AMEX is not impemented yet.'.format(self.module_name)) # TODO
        return False
