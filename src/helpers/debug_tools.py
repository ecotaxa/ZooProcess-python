

# my Dict assert
def myDictAssert(a:dict,b:dict):
    for i in a:
        if i in b:
            # assert a[i] == b[i]
            dump(a[i])
            dump(b[i])
            assert a[i]['object_id'] == b[i]['object_id']
            assert a[i]['img_file_name'] == b[i]['img_file_name']
            assert a[i]['img_rank'] == b[i]['img_rank']
            assert a[i]['path'] == b[i]['path']
        else:
            variable = "b"
            variable_name = retrieve_name(b)
            if not len(variable_name): variable=variable_name[0]
            raise Exception("key '" + i + "' don't exist in " + variable) 


# print tools

def dumpclean(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print (k)
                dumpclean(v)
            else:
                print ('%s : %s' % (k, v))
    elif isinstance(obj, list):
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print (v)
    else:
        print (obj)


def to_json(obj):
    import json
    print(json.dumps(obj, indent = 4))


import sys
def dump(obj, nested_level=0, output=sys.stdout , name=True):
    if name: 
        variable_names = mod_retrieve_name(obj)
        if len(variable_names):
            print(variable_names[0] + ":")
    spacing = '   '
    if isinstance(obj, dict):
        print ( '%s{' % ((nested_level) * spacing), file=sys.stderr )
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print ('%s%s:' % ((nested_level + 1) * spacing, k), file=sys.stderr)
                dump(v, nested_level + 1, output, name=False)
            else:
                print ( '%s%s: %s' % ((nested_level + 1) * spacing, k, v), file=sys.stderr)
        print ( '%s}' % (nested_level * spacing) , file=sys.stderr )
    elif isinstance(obj, list):
        print ( '%s[' % ((nested_level) * spacing), file=sys.stderr)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output, name=False)
            else:
                print ('%s%s' % ((nested_level + 1) * spacing, v) , file=sys.stderr)
        print ( '%s]' % ((nested_level) * spacing), file=sys.stderr)
    else:
        print ( '%s%s' % (nested_level * spacing, obj), file=sys.stderr)


# change namecr to '\n' permit to show some issue
def dump_structure(obj, nested_level=0, output=sys.stdout, name=True, namecr=""):
    import pandas as pd

    if name: 
        variable_names = mod_retrieve_name(obj)
        if len(variable_names):
            print(variable_names[0] + ":")
    spacing = '   '
    if isinstance(obj, dict):
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print ('%s%s:' % ((nested_level + 1) * spacing, k), file=sys.stderr)
                dump_structure(v, nested_level + 1, output, name=False)
            else:
                print ( '%s%s: %s' % ((nested_level + 1) * spacing, k, v), file=sys.stderr)
    elif isinstance(obj, list):
        print ( '%s[' % ((nested_level) * spacing), file=sys.stderr)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump_structure(v, nested_level + 1, output, name=False)
            else:
                print ('%s%s' % ((nested_level + 1) * spacing, v) , file=sys.stderr)
        print ( '%s]' % ((nested_level) * spacing), file=sys.stderr)
    elif isinstance(obj, pd.DataFrame):
            print ( 'Dataframe', file=sys.stderr)
    else:
        print ( '%s%s' % (nested_level * spacing, obj), file=sys.stderr)

# pip install PyYAML
def to_yaml(obj):
    import yaml
    print(yaml.dump(obj))


def _pprint(obj):
    import pprint
    pprint.pprint(obj, width=1)

def main():
    foo = {'A':{'size':70,
        'color':2},
        'B':{'size':60,
        'color':3}}

    print('dumpclean')
    dumpclean(foo)
    print("-------------------------------")
    print('to_json')
    to_json(foo)
    print("-------------------------------")
    print('dump')
    dump(foo)
    # print("-------------------------------")
    # print('to_yaml')
    # to_yaml(foo)
    print("-------------------------------")
    print('pprint')
    _pprint(foo)


import inspect
def retrieve_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]
 
def mod_retrieve_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]
 
def retrieve_name2(var):
        """
        Gets the name of var. Does it from the out most frame inner-wards.
        :param var: variable to get name from.
        :return: string
        """
        for fi in reversed(inspect.stack()):
            names = [var_name for var_name, var_val in fi.frame.f_locals.items() if var_val is var]
            if len(names) > 0:
                return names[0]

def foo(bar):
    print (retrieve_name(bar))
    print (mod_retrieve_name(bar))
 

def test():

    x, y, z = 1, 2, 3
    print(retrieve_name(y))
    foo(x)





if __name__ == '__main__':
    main()
    # test()


