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
from mdamodules import MdaModule
from mdamodules import MdaErrorCode
from mdamodules import MdaError

################################################################################
class MdaChkRcptto(MdaModule):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            if not self.options.check_required_modules(['INFOSSOURCES'], formodule=module_name):
                raise MdaError(MdaErrorCode()['MDA_ERR_NOTLOADED'], 'Some required modules are not loaded')
            self.options.get_module('INFOSSOURCES').CHKRCPTTO_init_confs()
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise
    
    ########################################
    def run(self, rcptto):
        return self.options.get_module('INFOSSOURCES').CHKRCPTTO_find_local_user_in_sources(rcptto)
