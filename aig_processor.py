# shit first pass at techmapping w/ AIGs and beam search
from aigsim import Model, Reader
from sympy import symbols, Not, And
from sympy.logic.boolalg import truth_table, sympify
from itertools import product
from collections import defaultdict
class CutWrapper:
    def __init__(self, node, cut):
        self.node = node
        self.cut = cut
        # self.function contains truth table, phase, and N Canonical Form
        self.function = None
    def print_cut(self):
        # self.node.printSelf()
        print(f"{self.node.lit}-> k= {len(list(self.cut))}", end=': ')
        for j in self.cut:
            print(j.lit, end = ', ')
        print(self.function)
        
    def set_function(self, function):
        self.function = function

def better_truth_table(expression, variables, k):
    # assert(len(variables) <= k)
    var_ordering = list(reversed(variables))
    elementary_variables = []
    tt_out = []
    for vals in product([0,1], repeat=k):
        elementary_variables = list(vals)[k - len(variables):]
        matching = dict(zip(var_ordering, elementary_variables))
        tt_out.append(int(bool(expression.subs(matching))))
    return tt_out

def symbolic_output(symbol, variables, k):
    if(len(variables) > 1):
        outputs = {}
        # I believe this is where the issue lies?
        # tt = lambda x,y: [int(bool(i)) for i in list(better_truth_table(x, y, 5))]
        # print(tt(symbol, variables))
        # print(better_truth_table(symbol,variables, 5))
        # exit(-1)
        canonicals = []
        for vals in product([0,1], repeat=len(variables)):
            phase_shift = symbol
            for idx, j in enumerate(vals):
                if(j):
                    phase_shift = phase_shift.subs(variables[idx], Not(variables[idx]))
            ps = better_truth_table(phase_shift, variables, k)
            canonicals.append((int(''.join(map(str, ps)), 2), list(vals), ps))
        return (symbol, better_truth_table(symbol,variables, k), min(canonicals, key = lambda t: t[0]))
    return

class CellFunction:
    def __init__(self, gate_name, inputs, outputs, function):
        self.gate_name = gate_name
        self.inputs = inputs
        self.outputs = outputs
        self.function = function
        self.truth_table = None
        self.canonicals = None
    def __repr__(self):
        return f"{self.gate_name}"
    

class CellTable:
    def __init__(self, cell_fns, k):
        # Go through list of cell functions,
        # make a table -> {N-canonical form : (CellFunction, phase)}
        self.matching_table = defaultdict(list)
        for i in cell_fns:
            cell_input_symbols = symbols(i.inputs)
            # self.cell_output_symbols = symbols(tuple(i.outputs))

            for j in i.function:
                cell_function_symbols = sympify(j[0][1:].replace('!', '~'))
                if cell_function_symbols != None:
                    i.truth_table, i.canonicals = cell_function_symbols, symbolic_output(cell_function_symbols, cell_input_symbols, k)
                    if i.canonicals is not None:
                        if i.canonicals[2][0] not in self.matching_table.keys(): self.matching_table[i.canonicals[2][0]] = [i]
                        else: self.matching_table[i.canonicals[2][0]].append(i)


def ingest_fspec(fspec):
    capture = False
    cell_capture = []
    cell_functions = []
    for i in fspec.splitlines():
        if capture:
            cell_capture.append(i)
        if '{' in i:
            capture = True
            cell_capture.append(i.split()[1])
        if '}' in i:
            capture = False
            # ignore gates that don't have a function
            if len(cell_capture) > 2:
                gate_name = cell_capture[0]
                cell_capture = cell_capture[1:]
                inputs = cell_capture[0].split()[1:]
                cell_capture = cell_capture[1:]
                outputs = []
                functions = []
                while cell_capture[0] != '}':
                    if 'Output' in cell_capture[0]:
                        outputs.append(cell_capture[0].split()[1:])
                    elif 'Function' in cell_capture[0]:
                        functions.append(cell_capture[0].split(':')[1:])
                    cell_capture = cell_capture[1:]
                cfn = CellFunction(gate_name, inputs, outputs, functions)
                cell_functions.append(cfn)
            cell_capture = []
    return cell_functions
            
def print_cutset(cutset):
    for po in cutset.keys():
        # print(len(cutset[po][-7]))
        print("ROOT NODE: ", end='')
        po.printSelf()
        for cut in cutset[po]:
            print(f"k = {len(cut)}")
            for j in list(cut):
                j.printSelf();
            print('-=-=-=-=-=-=-=-=-')
        print('_____________________________')
            

def gen_network_cuts(graph, k):
    # cuts = {}
    network_cutset = {}
    for output in graph.outputs:
        gen_node_cuts(graph, output.myInput, k, network_cutset)
    return network_cutset

def gen_node_cuts(graph, node, k, cutset):
    if node in graph.inputs:
        return [{node}]

    if node in cutset:
        return cutset[node]


    cuts1 = gen_node_cuts(graph, node.in1, k, cutset)
    cuts2 = gen_node_cuts(graph, node.in0, k, cutset)

    result = merge_cut_sets(cuts1, cuts2, k)
    result.extend([{node}])
    cutset[node] = result
    return result

def merge_cut_sets(set1, set2, k):
    result = []
    for cut1 in set1:
        for cut2 in set2:
            merged_cut = cut1.union(cut2)
            if len(merged_cut) <= k:
                result.append(merged_cut)
    return result


def cut_functions(cut, graph, k):
    sb = symbols(f"a0:{len(cut.cut)}")
    functions = dict(zip(cut.cut, sb))
    def traverse(node):
        if node in cut.cut:
            return node
        a = traverse(node.in1)
        b = traverse(node.in0)
        var_a = functions[a]
        if(node.in1Neg):
            var_a = ~var_a
        var_b = functions[b]
        if(node.in0Neg):
            var_b = ~var_b
        functions[node] = var_a & var_b
        return node
    traverse(cut.node)
    return symbolic_output(functions[cut.node], list(sb), k)

def gen_functions(cutset, m, k):
    funs = []
    for i in cutset:
        for j in list(cutset[i]):
            cut = CutWrapper(i, j)
            cfns = cut_functions(cut, m, k)
            if cfns:
                cut.set_function(cfns)
                funs.append(cut)
    return funs

if __name__ == '__main__':
    r = Reader()
    r.openFile("./examples/example.aag")
    m = Model()
    r.readHeader(m)
    r.readModel(m)
    r.procModelNames(m)
    k = 4
    cutset = gen_network_cuts(m, k)
    funs = gen_functions(cutset, m, k)
    ct = CellTable(ingest_fspec(open('./out.fspec').read()), k)
    for i in funs:
        i.print_cut()
        out = ct.matching_table[i.function[2][0]]
        print(out)
        print('----------------------------------------------------------------------------------------------------------------')