'''
This file is part of INES FLEX - 
INES (Integrated Energy Systems) FLexibility Energy eXchange

INES FLEX is free software: You can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

INES FLEX is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2021
Department of Integrated Energy Systems, University of Kassel,
Kassel, Germany

--

Start the DSO test client service directly.

Set env. var. FLEX_SERVER (default: gyges.iee.fraunhofer.de/flex) and 
optionally DSO_LOGLEVEL (default: INFO)

--

Created on 02.02.2021

@author: Sascha Holzhauer
'''

import dsoTestClient as dso
import os
import logging
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import secrets_local

if __name__ == '__main__':
    flexserver = os.getenv('FLEX_SERVER', flexserver_default)        
    loglevel = os.getenv('DSO_LOGLEVEL','INFO')
    
    dso = dso.DsoTestClient(flexserver, loglevel = loglevel)
    dso.run()