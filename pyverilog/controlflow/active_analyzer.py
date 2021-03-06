#-------------------------------------------------------------------------------
# active_analyzer.py
#
# Active condition list generator from Verilog Definitions
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import print_function
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
import pyverilog.utils.inference as inference
import pyverilog.dataflow.reorder as reorder
from pyverilog.dataflow.dataflow import *
import pyverilog.controlflow.splitter as splitter
import pyverilog.controlflow.transition as transition
from pyverilog.controlflow.controlflow_analyzer import VerilogControlflowAnalyzer

class VerilogActiveConditionAnalyzer(VerilogControlflowAnalyzer):
    def __init__(self, topmodule, terms, binddict, 
                 resolved_terms, resolved_binddict, constlist):
        VerilogControlflowAnalyzer.__init__(self, topmodule, terms, binddict, 
                                            resolved_terms, resolved_binddict, constlist)
        self.fsm_loops, self.fsms = self.getLoops()

    ############################################################################
    def getActiveConditions(self, termname, condition=splitter.active_constant):
        if not termname in self.resolved_binddict: return {}
        tree = self.makeTree(termname)
        funcdict = splitter.split(tree)
        funcdict = splitter.filter(funcdict, termname, condition)
        funcdict = splitter.remove_reset_condition(funcdict)

        if len(funcdict) == 1 and len(list(funcdict.keys())[0]) == 0:
            func = funcdict.values()[0]
            return {termname : ( ('any', None), )}

        active_conditions = {}
        active_conditions_size = 0
        for fsm_sig in self.fsms.keys():
            rslt = self.getActiveConditions_fsm(fsm_sig, funcdict)
            if len(rslt) > 0: active_conditions[fsm_sig] = rslt
            active_conditions_size += len(rslt)

        if active_conditions_size == 0:
            rslt = self.getActiveConditions_fsm(termname, funcdict)
            if len(rslt) > 0: active_conditions[termname] = rslt

        return active_conditions

    def getActiveConditions_fsm(self, fsm_sig, funcdict):
        # returns a list of some (state, transcond) pairs
        active_conditions = []
        fsm_sig_width = self.getWidth(fsm_sig)
        for condlist, func in sorted(funcdict.items(), key=lambda x:len(x[0])):
            node = transition.walkCondlist(condlist, fsm_sig, fsm_sig_width)
            state_node_list = []
            if isinstance(node, transition.StateNodeList):
                for n in node.nodelist: state_node_list.append(n)
            elif node:
                state_node_list.append(node)

            for state_node in state_node_list:
                #if state_node.isany:
                #    active_conditions.append( ('any', state_node.transcond) )
                for rs, re in state_node.range_pairs:
                    for state in range(rs, re+1):
                        transcond = self.optimizer.optimize(state_node.transcond)
                        if isinstance(transcond, DFEvalValue) and transcond.value == 0: continue
                        active_conditions.append( (state, transcond) )
        return tuple(active_conditions)
            
################################################################################
if __name__ == '__main__':
    from optparse import OptionParser
    import pyverilog.utils.util as util
    from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
    from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
    INFO = "Active condition analyzer"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python active_analyzer.py -t TOPMODULE file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()
    
    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-t","--top",dest="topmodule",
                         default="TOP",help="Top module, Default=TOP")
    optparser.add_option("-s","--search",dest="searchtarget",action="append",
                         default=[],help="Search Target Signal")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    analyzer = VerilogDataflowAnalyzer(filelist, options.topmodule)
    analyzer.generate()

    directives = analyzer.get_directives()
    terms = analyzer.getTerms()
    binddict = analyzer.getBinddict()

    optimizer = VerilogDataflowOptimizer(terms, binddict)

    optimizer.resolveConstant()
    resolved_terms = optimizer.getResolvedTerms()
    resolved_binddict = optimizer.getResolvedBinddict()
    constlist = optimizer.getConstlist()

    canalyzer = VerilogActiveConditionAnalyzer(options.topmodule, terms, binddict, 
                                               resolved_terms, resolved_binddict, constlist)

    for target in options.searchtarget:
        signal = util.toTermname(target)

        active_conditions = canalyzer.getActiveConditions( signal )
        #active_conditions = canalyzer.getActiveConditions( signal, condition=splitter.active_modify )
        #active_conditions = canalyzer.getActiveConditions( signal, condition=splitter.active_unmodify )

        print('Active Cases: %s' % signal)
        for fsm_sig, active_conditions in sorted(active_conditions.items(), key=lambda x:str(x[0])):
            print('FSM: %s' % fsm_sig)
            for state, active_condition in sorted(active_conditions, key=lambda x:str(x[0])):
                s = []
                s.append('state: %d -> ' % state)
                if active_condition: s.append(active_condition.tocode())
                else: s.append('empty')
                print(''.join(s))
