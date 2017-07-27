#! /usr/bin/env python
"""
Create the API Wrapper functions
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
** When generating API, run this script THIRD. **

This generates the complete library of function wrappers for the FRED
win32 subroutines, functions and datastructures. These functions should
be the most complete way to access FRED through the API with call signatures
equivalent to their counterparts within FRED.

TODO: Add a TextWindowPrint() subroutine to call a CreatLib() wrapped
VBScript Print() command for printing to the FRED output window.
TODO: Switch to using jinja2 templates instead of string formatting.
"""
import os
import re # Regex module
import yaml
import datetime
import codecs

import utils_parse as utils
import glovars

# Setup to use breakpt() for droppping into ipdb:
from IPython.core.debugger import Tracer
breakpt = Tracer()

# Indentation whitespace:
I1 = " " * 4
I2 = I1 * 2
I3 = I1 + I2

TIMENOW = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Regex for matching on parenthesis with or without whitespace
PARMAT = re.compile('\s*\(\s*\)\s*')

# Class definition string
CLASTR='''#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provide class to wrap all available FRED commands
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------

{} - File generated

WARNING - This file is automatically generated by script03_apiwrapgen.py.
Customizing functions here will override intended API function.
Also any changes will be lost the next time script03_apiwrapgen.py is run.

"""
try:
    import win32com.client as w32
except:
    # Load a dummy
    print("WARNING: win32com not available. Loading dummy library.")
    from w32dummy import WinMethods
    w32 = WinMethods()

class Wrap(object):
    """
    Class for wrapping all of the FRED functions, subroutines and
    datastructures in one place with a consistent API and minimal quirks.

    Using this class for FRED programming may not be the most efficient
    computationally, but it does provide an easier transition for
    controlling FRED through python then just using the raw win32com API.

    Quirks that are caused by problematic parameter passing through the
    w32 API and/or inconsistent return structures are averted by wrapping
    all functions/subroutines with CreateLib().

    Also quite handy to have around for quick access to documentation when
    using IPython.

    If imported into the global namespace, allows writing scripts that are
    nearly execution compatible with native FRED VBScript.
    """
    def __init__(self, dobj):
        self._dobj = dobj

    @property
    def dobj(self):
        """
        Attribute property for the FRED COM Interface document object
        """
        return self._dobj
'''.format(TIMENOW)

def main():
    """
    Encapsulate script procedural body here so it can be externally
    referenced as <filename>.main or automatically invoked from the
    if __name__ == "__main__"" statement when the script is run directly.
    """
    # Get the API Building data structure
    # apidat is a dict with the keys of available command names and the
    # values each a dict with keys: cmdtype, descr, returns, sig
    apidat = utils.readyaml(glovars.APIFILEPATH)
    # Get the documentation we have for everything
    # docdat is a dict with the keys of available command names and the
    # values each an OrderedDict key/valued on heading/docstring
    docdat = utils.readyaml(glovars.DOCFILEPATH)

    # For running on a small set of commands:
    '''
    cmdnames = {
        'GetUnits', # 0 Funct args; Ret: String
        'FindFullName', # 1 Funct args: String; Ret: Long
        'EnergyDensity', # 4 Funct args: Long, Long, T_ANALYSIS, Double; Ret: Long
        'ARNDeleteAllNodes', # 0 Sub args: NONE
        'SetUnits', # 1 Sub arg: String
        'GetEntity', # 2 Sub args: Long, T_ENTITY
        'GetTextPosition', # 2 Sub args: Long, Long
        'T_ENTITY', # 7 Datastruct args: Long, String, String, Boolean x 4
        }
    '''
    # For running on all available commands:
    cmdnames = apidat.keys()
    fid = codecs.open(glovars.PYAPIPATH, 'w', 'utf-8')
    fid.write(CLASTR)
    print("\nWrapping commands in python...")
    for cmdname in cmdnames:
        cmdtype = apidat[cmdname]['cmdtype']
        if cmdtype == 'unknown':
            print("... unknown command: {}. SKIPPING".format(cmdname))
            continue
        print("... wrapping {}".format(cmdname))
        descstr = "Wrapper for FRED {} {}.\n".format(cmdname, cmdtype.upper())
        if cmdtype == 'datastruct':
            descstr += (I2 + 'Does not require all parameters to be '
                      'set when invoked.\n')
        else:
            descstr += (I2 + 'Requires all parameters to be set when invoked.\n'
                      .format(cmdtype.upper()))
        descstr += "\n"
        descstr += I2
        descstr += utils.wrap_longlines(apidat[cmdname]['descr'], indent=I2)
        sigitems = apidat[cmdname]['sig']
        params = [_[0] for _ in sigitems]
        # Parameters that have parenthesis indicate array-like variables.
        # Strip the parenthesis but include an array annotation
        annots = {}
        newparams = {} # Key newparams on the original params
        for p in params:
            if PARMAT.search(p) is not None:
                newparams[p] = PARMAT.sub('', p)
                annots[p] = 'Array-like of '
            else:
                newparams[p] = p
                annots[p] = ''

        docstr = utils.fmt_docstr(docdat[cmdname], indent=I2)
        retstr = ''
        # Return string heading:
        rethdg =  "\n"
        rethdg += I2 + 'Returns\n'
        rethdg += I2 + '-------\n'
        rlist = apidat[cmdname]['returns']
        if apidat[cmdname]['cmdtype'] == 'function':
            if apidat[cmdname]['returns'] != []:
                # A function should always have a return, always include rethdg
                retstr += rethdg
                rname, rtype = rlist
                rtype = utils.vb2pytype(rtype, rettype='repr')
                retstr += I2 + '{}: {}\n'.format(rname, rtype)
        elif apidat[cmdname]['cmdtype'] == 'subroutine':
            # Only make a return string if something is returned
            if 0 < len(sigitems) or 0 < len(rlist):
                retstr += rethdg
                retstr += I2
                # If subroutine has a return values, we are treating a FRED
                # function like a subroutine and want to get the return value
                # along with all of the signature parameters
                if 0 < len(rlist):
                    sigits = [rlist]
                else:
                    sigits = list()
                if 0 < len(sigitems):
                    sigits.extend(apidat[cmdname]['sig'])
                if len(sigits) > 1:
                    # Multiple values returned in a list
                    retstr += '['
                rstr = []
                for rn, rt in sigits:
                    rstr.append('{}: {}'.format(rn,
                                         utils.vb2pytype(rt, rettype='repr')))
                retstr += ", ".join(rstr)
                if len(sigits) > 1:
                    # Multiple values returned in a list
                    retstr += ']'
                retstr += "\n"
        elif apidat[cmdname]['cmdtype'] == 'datastruct':
            # A datatsruct always has a return, always include rethdg
            retstr += rethdg
            retstr += I2 + "datastruct: <com_record {}>\n".format(cmdname)
        fid.write(I1 + "# " + "=-"*36 + "=\n")
        params.insert(0, "self")
        newparams['self'] = "self"
        paramlist = [newparams[_] for _ in params]
        # Set a None default for datastruct command parameters so it's not
        # an error to not supply an arg (except to self)
        arglist = []
        for li in paramlist:
            if cmdtype == 'datastruct' and li != "self":
                arglist.append(li + "=None")
            else:
                arglist.append(li)
        # Python function definition:
        fid.write(I1 + "def {}({}):\n".format(cmdname, utils.wrap_longlines(
                ", ".join(arglist), ncols=50, indent=" "*12)))
        fid.write(I2 + 'r"""\n') # Use raw docstring in case of weird chars
        fid.write(I2 + 'Python API documentation:\n')
        fid.write(I2 + '=========================\n')
        fid.write(I2 + '{}\n'.format(descstr))
        fid.write('\n')
        # Skip param[0] "self" parameter:
        if len(params[1:]) > 0:
            fid.write(I2 + 'Parameters\n')
            fid.write(I2 + '----------\n')
            for par, typ in sigitems:
                paramdoc = utils.vb2pytype(typ, rettype='repr')
                fid.write(I2 + '{}: {}{}\n'.format(newparams[par],
                                                   annots[par], paramdoc))
        fid.write(retstr)
        fid.write('\n')
        fid.write(I2 + 'FRED documentation:\n')
        fid.write(I2 + '===================\n')
        fid.write(docstr)
        fid.write(I2 + '"""\n')
        # For functions/subroutines, use the VBScript wrappers.
        # For datastructures, use w32.Record.
        if apidat[cmdname]['cmdtype'] == 'datastruct':
            fid.write(I2 + 'dstruct = w32.Record("{}", self._dobj)\n'.
                           format(cmdname))
            # Use each parameter (except self) to set the dstruct attributes
            # only if it was supplied on the call (parameter is not None).
            for p in paramlist[1:]:
                fid.write(I2 + 'if {} is not None:\n'.format(p))
                fid.write(I2 + I1 + 'setattr(dstruct, "{}", {})\n'.
                                    format(p, p))
            fid.write(I2 + 'return dstruct\n')
        else:
            # Get parameter string with all but self:
            paramstr = utils.wrap_longlines(", ".join(paramlist[1:]),
                                            ncols=50, indent=" "*12)
            # Also handle special case when VBScript funct/sub does not take
            # any parameters, we pass it a dummy variable
            if paramstr == '':
                paramstr = 'None'
            stubpath = os.path.join(glovars.STUBDIR, cmdname + '.frs')
            # Instead of escaping backslashes, specify the string as raw
            fid.write(I2 + 'lib = self._dobj.CreateLib(r"{}")\n'
                      .format(stubpath))
            fid.write(I2 + 'return lib.libfunct({})\n'.format(paramstr))
    fid.close()

if __name__ == "__main__":
    # If this script is invoked directly (not imported), execute main()
    main()