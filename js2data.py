#!/usr/bin/env python
from __future__ import print_function

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import json
from random import choice, uniform, randint, getrandbits
import string
from math import ceil
from datetime import datetime
from importlib import import_module

try:
    import exrex
except ImportError:
    print("Module exrex not present - please run 'pip install exrex'!")
    sys.exit(100)
    
try:
    import pytz
except ImportError:
    print("Module pytz not present - please run 'pip install pytz'")
    sys.exit(101)
    
# Process any command line arguments.
parser = ArgumentParser(description='Generate sample data from JSON Schema', formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-d', '--debug', default=False, action='store_true', help='Turn debugging on (default: %(default)s).')
parser.add_argument('-m', '--module', default=['report'], nargs='*', help='Name of module to import - can be more than one instance (default: %(default)s).')
parser.add_argument('-a', '--array', default=0, type=int, help='Maximum array count supported; 0 is no limit (default: %(default)s).')
parser.add_argument('-p', '--print', default=False, action='store_true', help='Print out a formatted version of the generated JSON data (default: %(default)s).')
parser.add_argument('-o', '--output', default=None, help='If present output JSON data to file (default: %(default)s).')
parser.add_argument('schema')
args = parser.parse_args()

# Bring in the module definitions for generating sample data.
sys.path.append('.')
modules = map(__import__, args.module)

def execute_function(func_name, arglist):
    for mod in modules:
        func_ptr = getattr(mod, func_name, None)
        if func_ptr:
            return func_ptr(globals(), locals(),arglist=arglist)
    print('Trying to execute function %s and not found!' % (func_name))
    return "***FAILED %s" % (func_name) 

def process_string(x):
    # The input looks like one of these:
    #
    # func
    # func;arg1,arg2,...
    #
    # Where func is the function name, and argN are string arguments to pass
    # into the function when it is executed.
    xs = x.split(';')
    if len(xs) == 2:
        # We have some arguments, so parse it.
        arglist = xs[1].split(',')
    else:
        arglist = None
    return xs[0], arglist

def process_function(spec):
    # We check to see if the description string has the function stuff in it. If so
    # we will process it.
    rc = None
    if 'description' in spec:
        rc = spec['description'].split('>>')[1].split('<<')[0] if spec['description'].startswith('>>') else None
    elif 'function' in spec:
        rc = spec['function']
    return rc

# For each of the processing types we ignore things like title, id and schema. They
# don't really add any value to the generated data. What we focus on is the type, definitions, etc.
#
# Description has a specific format - it tells us how to generate the data. If there is no description
# there is a default for each type.

def build_by_ref(homespec, spec):
    if spec.startswith('#'):
        # Local reference to our file... so get the specification for what we are building...
        temp = spec.split('/')
        spec = homespec[temp[1]][temp[2]]
        return built_by_type(homespec, spec)
    else:
        print( "Specification %s not yet supported!" &(spec,))
        return None

def build_array(homespec, spec):
 
    # Set the min and max count of items in the array.
    minItems = int(spec['minItems']) if 'minItems' in spec else 0
    maxItems = int(spec['maxItems']) if 'maxItems' in spec else sys.maxsize
    if args.array:
        maxItems = min(maxItems, args.array)
        
    # Figure how many we are going to process...this is a random number of items.
    noitems = randint(minItems, maxItems)    
    
    # The array object to be returned
    object = []
    for i in xrange(noitems):
        # For the time being we only support list validation mode. 
        if '$ref' in spec['items']:
            object.append(build_by_ref(homespec, spec['items']['$ref']))
        elif 1: # Other types...
            pass
    return object

def build_string(homespec, spec):
    
    def EnumGenerator(elist):
        # Pick a random entry; we force the item to be a string just in case we 
        # have a list of numbers.
        return str(choice(elist))
    
    def stringGenerator(minLength,maxLength):
        # Figure out what length string me need. 
        if minLength < 0 :
            minLength = 0
        if maxLength < 0:
            maxLength = 4096
        length = int(ceil(uniform(minLength, maxLength)))
        return ''.join(choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def datetime_func():
        d = datetime.utcnow()
        dt_with_tz = d.replace(tzinfo=pytz.UTC)
        return dt_with_tz.isoformat()

    def email_func():
        pass
    def hostname_func():
        pass
    def ipv4_func():
        pass
    def ipv6_func():
        pass
    def url_func():
        pass
    format_funcs = {'date-time':datetime_func, 'email':email_func, 'hostname':hostname_func,
                    'ipv4':ipv4_func, 'ipv6':ipv6_func, 'url':url_func}
    def do_format(fmt):
        if fmt.lower() not in format_funcs.keys():
            print("Invalid format %s encountered." % (fmt))
            return "???????"
        else:
            return format_funcs[fmt.lower()]()
    
    # This is a general purpose string operation! So we need to figure out if we are going to 
    # execute a specific function or the general string generator.
    function = None
    if 'function' in spec:
        # The user specified a function item telling us what to execute.
        function = spec['function']
    elif 'description' in spec and spec['description'].startswith('>>'):
        # We have a description with a function definition in the description.
        function = spec['description'].split('>>')[1].split('<<')[0]
        
    # Figure out the length of the string needed. If present they may be ignored 
    # when the format item is present!
    maxLength = int(spec['maxLength'] if 'maxLength' in spec else '-1')
    minLength = int(spec['minLength'] if 'minLength' in spec else '-1')
    
    # See if we have an enum thing...
    enumlist = spec['enum'] if 'enum' in spec else None

    # Specific functions always over-ride format. in the case of no specific
    # function definitions we will look for a format item; if present that 
    # will define the function. Otherwise we just use the default string
    # generator.
    if function:
        # Do it...
        funcname, arglist = process_string(function)
        genstr = execute_function(funcname, arglist)
    else:
        # No function has been specified by the user. We need to see if we have
        # a format item. If so we use it. If not we use the default string generator.
        if 'format' in spec:
            # This overrides everything else. We don't need a min or max length.
            genstr =  do_format(spec['format'])
        elif enumlist:
            genstr = EnumGenerator(enumlist)
        else:
            # Do it...
            genstr =  stringGenerator(minLength, maxLength)
    return genstr
            
def build_integer(homespec, spec):
    # We are going to generate an integer. So figure out the minimum and maximum
    # values.
    #
    function = None
    if 'function' in spec:
        # The user specified a function item telling us what to execute.
        function = spec['function']
    elif 'description' in spec and spec['description'].startswith('>>'):
        # We have a description with a function definition in the description.
        function = spec['description'].split('>>')[1].split('<<')[0]
    if function:
        # Do it...
        funcname, arglist = process_string(function)
        genstr = execute_function(funcname, arglist)
    else:
        # Note: in Python2.x we should use maxint but we use maxsize since Python3.x doesn't
        # have it. Instead both support maxsize.
        minValue = int(spec['minimum']) if 'minimum' in spec else (-sys.maxsize-1)
        maxValue = int(spec['maximum']) if 'maximum' in spec else sys.maxsize
        
        # See if we have exclusive value flags set...
        if bool(spec['exclusiveMinimum']) if 'exclusiveMinimum' in spec else False:
            minValue += 1
        if bool(spec['exclusiveMaximum']) if 'exclusiveMaximum' in spec else False:
            maxValue -= 1
            
        # Finally, see if multipleOf is set.
        multipleOf = int(spec['multipleOf']) if 'multipleOf' in spec else 1
        
        genstr = str(randint(minValue/multipleOf, maxValue/multipleOf))*multipleOf
    return genstr

def build_number(homespec, spec):
    # We are going to generate an real number. So figure out the minimum and maximum
    # values. If we have a function, we will use it. Otherwise we generate a random
    # number in some range.
    function = None
    if 'function' in spec:
        # The user specified a function item telling us what to execute.
        function = spec['function']
    elif 'description' in spec and spec['description'].startswith('>>'):
        # We have a description with a function definition in the description.
        function = spec['description'].split('>>')[1].split('<<')[0]
    if function:
        # Do it...
        funcname, arglist = process_string(function)
        genstr = execute_function(funcname, arglist)
    else:  
        #
        # Note: in Python2.x we should use maxint but we use maxsize since Python3.x doesn't
        # have it. Instead both support maxsize.
        minValue = float(spec['minimum']) if 'minimum' in spec else sys.float_info.min
        maxValue = float(spec['maximum']) if 'maximum' in spec else sys.float_info.max
        
        # See if we have exclusive value flags set...notice we aren't too particular
        # about the min and max values with exclusive. We just need to be close.
        if bool(spec['exclusiveMinimum']) if 'exclusiveMinimum' in spec else False:
            minValue += 1.0
        if bool(spec['exclusiveMaximum']) if 'exclusiveMaximum' in spec else False:
            maxValue -= 1.0
                
        genstr = str(uniform(minValue, maxValue))
    return genstr

def build_object(homespec, spec):
    # We have an objecet so we are expecting to see some properties ...
    object = {}
    if 'properties' in spec:
        for prop in spec['properties']:
            if 'anyOf' in spec['properties'][prop]:
                spec['properties'][prop]['type'] = 'anyOf'
            if 'oneOf' in spec['properties'][prop]:
                spec['properties'][prop]['type'] = 'oneOf'
            if 'type' not in spec['properties'][prop]:
                print("Property %s has no 'type' specification - ignored!" % (spec['properties'][prop]))
            else:
                # Generate it!
                if args.debug:
                    print("Processing property %s" % (prop,))
                object[prop] = json_type_processing[spec['properties'][prop]['type']](homespec, spec['properties'][prop])
    return object

def build_bool(homespec, spec):
    # We need to figure out if we are going to execute a specific function or the general string generator.
    function = None
    if 'function' in spec:
        # The user specified a function item telling us what to execute.
        function = spec['function']
    elif 'description' in spec and spec['description'].startswith('>>'):
        # We have a description with a function definition in the description.
        function = spec['description'].split('>>')[1].split('<<')[0]

    # If we have a function, we will use it to generate the value. Otherwise we randomly generate
    # a truth value.
    if function:
        # Do it...
        funcname, arglist = process_string(function)
        genstr = execute_function(funcname, arglist)
    else:
        genstr = str(bool(getrandbits(1)))
    return genstr
    
def build_null(homespec, spec):
    # We need to figure out if we are going to execute a specific function or the general string generator.
    function = None
    if 'function' in spec:
        # The user specified a function item telling us what to execute.
        function = spec['function']
    elif 'description' in spec and spec['description'].startswith('>>'):
        # We have a description with a function definition in the description.
        function = spec['description'].split('>>')[1].split('<<')[0]

    # If we have a function, we will use it to generate the value. Otherwise we randomly generate
    # a truth value.
    if function:
        # Do it...
        funcname, arglist = process_string(function)
        genstr = execute_function(funcname, arglist)
    else:
        genstr = str(None)
    return genstr

def build_anyOf(homespec, spec):
    list_of_any = spec['anyOf']
    which = choice(list_of_any)
    return build_by_ref(homespec, which['$ref'])

def build_oneOf(homespec, spec):
    pass


json_type_processing = {'array':build_array, 'string':build_string, 'integer':build_integer,
                        'number':build_number, 'object':build_object, 'boolean':build_bool, 
                        'null':build_null, 'anyOf':build_anyOf, 'oneOf':build_oneOf}

def built_by_type(homespec, spec):
    build_type = spec['type'] if 'type' in spec else 'object'
    return json_type_processing[build_type](homespec, spec)
                                
# Import the json schema into our program...
json_schema = json.load(open(args.schema,'r'))

# For the top object determine what we want...
json_top = built_by_type(json_schema, json_schema)

# Print out the formatted JSON data?
if args.print:
    print(json.dumps(json_top, indent=4, sort_keys=True))

# Output the data to some file?
if args.output:
    fp = open(args.output, 'w')
    json.dump(json_top, fp)
    fp.close()


        
        
        
