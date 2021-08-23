'''
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
