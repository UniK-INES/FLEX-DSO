'''
Created on 02.02.2021

@author: Sascha Holzhauer
'''
import dsoTestClient as dso
import os

if __name__ == '__main__':
    flexserver = os.environ.get('FLEX_SERVER')
    if flexserver is None:
        flexserver = secrets_local.flexserver_default
    dso = dso.DsoTestClient(flexserver)
    #dso.run()
    
    dso.setInactive()