import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = '../../testcode/'

expected = """\
(Bind dest:TOP.cnt \
tree:(Branch Cond:(Terminal TOP.RST) \
True:(Terminal TOP.cnt) False:(Terminal TOP.cnt)))
"""

def test():
    filelist = [codedir + 'signed_task.v']
    topmodule = 'TOP'
    noreorder = False
    nobind = False
    include = None
    define = None
    
    analyzer = VerilogDataflowAnalyzer(filelist, topmodule,
                                       noreorder=noreorder,
                                       nobind=nobind,
                                       preprocess_include=include,
                                       preprocess_define=define)
    analyzer.generate()

    directives = analyzer.get_directives()
    instances = analyzer.getInstances()
    terms = analyzer.getTerms()
    binddict = analyzer.getBinddict()

    output = []
    output.append(list(binddict.values())[0][0].tostr())
    output.append('\n')
            
    rslt = ''.join(output)

    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
