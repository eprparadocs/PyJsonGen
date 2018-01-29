from random import getrandbits, choice

swversions = {'consoleitem':'sw-console-v1.2',
              'instrumentitem':'sw-instrument-v1.2',
              'armitem':'sw-arm-v1.2',
              'toweritem':'sw-tower-v1.2'
              }
def swVer(glob, loc, arglist=None):
    return swversions[arglist[0]] if arglist else 'INVALID ARGUMENT LIST'

id = 0
def buttonid(glob, loc, arglist=None):
    global id
    genstr = 'buttonid-%s' % (id,)
    id += 1
    return genstr

hwid = 0
def HWid(glob, loc, arglist=None):
    global hwid
    genstr = 'hardware-id-%s' % (hwid,)
    hwid += 1
    return genstr

armid = 0
def ARMid(glob, loc, arglist=None):
    global armid
    genstr = 'arm-id-%s' % (armid,)
    armid += 1
    return genstr

def EinsteinID(glob, loc, arglist=None):
    return 'einstein-id-1'

def ButtonAction(glob, loc, arglist=None):
    return 'pushed' if getrandbits(1) else 'released'

widgetid = 0
def WidgetName(glob, loc, arglist=None):
    global widgetid
    genstr = 'widget%s' % (widgetid,)
    widgetid += 1
    return genstr

screenid = 0
def ScreenName(glob, loc, arglist=None):
    global screenid
    genstr = 'screen%s' % (screenid,)
    screenid += 1
    return genstr

def RandomValues(glob, loc, arglist=None):
    answers = [1,3.14159265, 100, 'Input 1', 'Input 2', 'Somemore input']
    return str( choice(answers) )

skuid = 0
def SKU(glob, loc, arglist=None):
    global skuid
    genstr = 'sku-%s' % (skuid,)
    skuid += 1
    return genstr


    