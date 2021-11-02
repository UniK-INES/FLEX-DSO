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
Created on 09.02.2021

@author: Sascha Holzhauer
'''
import logging
from re import match

def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

def extractLeadingInt(string):
    sb = ""
    for c in string:
        if not c.isdigit():
            break;
        sb = sb + c
    return int(sb)
    
def durationString2Millis(durationStr):
    matchesDayBased = match("^-\\d*[1-9]\\d*[dD]([0-1]\\d|2[0123]):[012345]\\d$", durationStr) != None
    matchesDurationBased = False if matchesDayBased else match("^(-?)(\\d*[1-9]\\d*[hH]|\\d*[1-9]\\d*[mM]|\\d*[1-9]\\d*[sS]|\\d*[1-9]\\d*[hH]\\d*[1-9]\\d*[mM])$", durationStr) != None
    if (not matchesDayBased) and not matchesDurationBased:
        logging.error("Illegal duration string: " + durationStr);
    if durationStr.startswith("-"):
        durationStr = durationStr[1:];
    lower = durationStr.lower();
    if matchesDayBased:
        nrDays = extractLeadingInt(durationStr);
        idx = lower.find('d');
        hours = extractLeadingInt(durationStr[idx+1:]);
        minutes = extractLeadingInt(durationStr.substring[idx+4:]);
        return ((nrDays * 24 + hours) * 60 + minutes) * 60 *1000
    else:    
        lower = durationStr.lower();
        hIdx = lower.find('h')
        mIdx = lower.find('m')
        sIdx = lower.find('s')
        firstNumIdx = 1 if durationStr.startswith("-", 0) else 0;
        if hIdx > 0:
            hours = extractLeadingInt(durationStr[firstNumIdx:]);
        else:
            hours = 0;
        if mIdx > 0:
            minutes = extractLeadingInt(durationStr[hIdx+1 if hIdx > 0 else firstNumIdx:])
        else:
            minutes = 0;
        if sIdx > 0:
            # when seconds included, only seconds are allowed (no hours and minutes)
            seconds = extractLeadingInt(durationStr[firstNumIdx:]);
        else:
            seconds = 0;
        return (hours * 60 + minutes) * (60 + seconds) *1000
