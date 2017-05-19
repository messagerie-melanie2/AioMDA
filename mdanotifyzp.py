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
import os
from mdamodules import MdaModule
#from mdamodules import MdaErrorCode
#from mdamodules import MdaError

################################################################################
class MdaNotifyZp(MdaModule):
    ########################################
    def __init__(self, module_name, options, confparser):
        try:
            super().__init__(module_name, options, confparser)
            self.notify_path = self.confparser.get(self.module_name, 'path', fallback='/var/cache/notifyzp/')
            notify_path_mod = self.confparser.get(self.module_name, 'mod', fallback='755')
            notify_path_owner = self.confparser.get(self.module_name, 'owner', fallback=None)
            create_dir = self.confparser.getboolean(self.module_name, 'createdir', fallback=True)
            self.init_dir(self.notify_path, mod=notify_path_mod, owner=notify_path_owner, create_dir=create_dir)
        except:
            print('{} - {}'.format(self.module_name, sys.exc_info()[0])) # TODO
            raise

    ########################################
    def run(self,  rcptto):
        try:
            filename = '{}/{}'.format(self.notify_path, rcptto)
            if not os.path.exists(filename):
                os.mknod(filename)
        except:
            self.log.error('{} - Error during run: {}'.format(self.module_name, sys.exc_info()[0]))

