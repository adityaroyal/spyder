# -*- coding: utf-8 -*-
#
# Copyright © 2009-2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Startup file used by ExternalPythonShell exclusively for IPython kernels
(see spyderlib/widgets/externalshell/pythonshell.py)"""

import sys
import os.path as osp


def sympy_config(version):
    """Sympy configuration"""
    
    lines = """
from __future__ import division
from sympy import *
x, y, z, t = symbols('x y z t')
k, m, n = symbols('k m n', integer=True)
f, g, h = symbols('f g h', cls=Function)
"""
    
    if version >= '0.7.2':
        extension = 'sympy.interactive.ipythonprinting'
    else:
        extension = 'sympyprinting'
    
    return lines, extension


def kernel_config():
    """Create a config object with IPython kernel options"""
    from IPython.config.loader import Config, load_pyconfig_files
    from IPython.core.application import get_ipython_dir
    from spyderlib.config import CONF
    
    # ---- IPython config ----
    try:
        profile_path = osp.join(get_ipython_dir(), 'profile_default')
        ip_cfg = load_pyconfig_files(['ipython_config.py',
                                      'ipython_qtconsole_config.py'],
                                      profile_path)
    except:
        ip_cfg = Config()
    
    # ---- Spyder config ----
    spy_cfg = Config()
    
    # Until we implement Issue 1052:
    # http://code.google.com/p/spyderlib/issues/detail?id=1052
    spy_cfg.InteractiveShell.xmode = 'Plain'
    
    # Pylab activation option
    pylab_o = CONF.get('ipython_console', 'pylab')
    
    # Automatically load Pylab and Numpy
    autoload_pylab_o = CONF.get('ipython_console', 'pylab/autoload')
    spy_cfg.IPKernelApp.pylab_import_all = pylab_o and autoload_pylab_o
    
    # Pylab backend configuration
    if pylab_o:
        backend_o = CONF.get('ipython_console', 'pylab/backend', 0)
        backends = {0: 'inline', 1: 'auto', 2: 'qt', 3: 'osx', 4: 'gtk',
                    5: 'wx', 6: 'tk'}
        spy_cfg.IPKernelApp.pylab = backends[backend_o]
        
        # Inline backend configuration
        if backends[backend_o] == 'inline':
           # Figure format
           format_o = CONF.get('ipython_console',
                               'pylab/inline/figure_format', 0)
           formats = {0: 'png', 1: 'svg'}
           spy_cfg.InlineBackend.figure_format = formats[format_o]
           
           # Resolution
           spy_cfg.InlineBackend.rc = {'figure.figsize': (6.0, 4.0),
                                   'savefig.dpi': 72,
                                   'font.size': 10,
                                   'figure.subplot.bottom': .125
                                   }
           resolution_o = CONF.get('ipython_console', 
                                   'pylab/inline/resolution')
           spy_cfg.InlineBackend.rc['savefig.dpi'] = resolution_o
           
           # Figure size
           width_o = float(CONF.get('ipython_console', 'pylab/inline/width'))
           height_o = float(CONF.get('ipython_console', 'pylab/inline/height'))
           spy_cfg.InlineBackend.rc['figure.figsize'] = (width_o, height_o)
    
    # Run lines of code at startup
    run_lines_o = CONF.get('ipython_console', 'startup/run_lines')
    if run_lines_o:
        spy_cfg.IPKernelApp.exec_lines = map(lambda x: x.strip(),
                                         run_lines_o.split(','))
    
    # Run a file at startup
    use_file_o = CONF.get('ipython_console', 'startup/use_run_file')
    run_file_o = CONF.get('ipython_console', 'startup/run_file')
    if use_file_o and run_file_o:
        spy_cfg.IPKernelApp.file_to_run = run_file_o
    
    # Autocall
    autocall_o = CONF.get('ipython_console', 'autocall')
    spy_cfg.ZMQInteractiveShell.autocall = autocall_o
    
    # Greedy completer
    greedy_o = CONF.get('ipython_console', 'greedy_completer')
    spy_cfg.IPCompleter.greedy = greedy_o
    
    # Sympy loading
    sympy_o = CONF.get('ipython_console', 'symbolic_math')
    if sympy_o:
        try:
            from sympy import __version__ as version
            lines, extension = sympy_config(version)
            if run_lines_o:
                spy_cfg.IPKernelApp.exec_lines.append(lines)
            else:
                spy_cfg.IPKernelApp.exec_lines = [lines]
            spy_cfg.IPKernelApp.extra_extension = extension
            spy_cfg.LaTeXTool.backends = ['dvipng', 'matplotlib']
        except ImportError:
            pass
    
    # Merge IPython and Spyder configs. Spyder prefs will have prevalence
    # over IPython ones
    ip_cfg._merge(spy_cfg)
    return ip_cfg


def set_edit_magic(shell):
    """Use %edit to open files in Spyder"""
    from spyderlib.utils import programs
    
    if programs.is_module_installed('IPython.frontend.qt', '>=0.13'):
        # For some users, trying to replace %edit with open_in_spyder could
        # give a crash when starting a kernel. I've seen it after updating
        # from 2.1
        try:
            shell.magics_manager.magics['line']['ed'] = \
              shell.magics_manager.magics['line']['edit']
            shell.magics_manager.magics['line']['edit'] = open_in_spyder
        except:
            pass
    else:
        # Don't wanna know how things were in previous versions
        pass


# Remove this module's path from sys.path:
try:
    sys.path.remove(osp.dirname(__file__))
except ValueError:
    pass

locals().pop('__file__')
__doc__ = ''
__name__ = '__main__'

# Add current directory to sys.path (like for any standard Python interpreter
# executed in interactive mode):
sys.path.insert(0, '')

# Fire up the kernel instance.
try:
    from IPython.zmq.ipkernel import IPKernelApp  # 0.13
except ImportError:
    from IPython.kernel.zmq.kernelapp import IPKernelApp  # 0.14

ipk_temp = IPKernelApp.instance()
ipk_temp.config = kernel_config()
ipk_temp.initialize()

__ipythonshell__ = ipk_temp.shell
set_edit_magic(__ipythonshell__)

#  Issue 977 : Since kernel.initialize() has completed execution, 
# we can now allow the monitor to communicate the availablility of 
# the kernel to accept front end connections.
__ipythonkernel__ = ipk_temp
del ipk_temp

# Start the (infinite) kernel event loop.
__ipythonkernel__.start()