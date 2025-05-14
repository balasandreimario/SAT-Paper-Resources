import sys, json
sys.setrecursionlimit(1500000)
recursive_calls = 0
unit_props = 0

def read_clauseset(path):
    clauseset = []
    num_vars = 0
    num_clauses = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c') or line.startswith('%'):
                continue
            if line.startswith('p cnf'):
                parts = line.split()
                num_vars = int(parts[2])
                num_clauses = int(parts[3])
                continue
            literals = list(map(int, line.split()))
            if literals and literals[-1] == 0:
                literals = literals[:-1]
            if literals:
                clauseset.append(literals)
    return clauseset, num_vars, num_clauses

def propagation(clauseset, literal):
    neg = -literal
    new_clauseset = []
    
    for clause in clauseset:
        if literal in clause:
            continue
        if neg in clause:
            new_clause = [lit for lit in clause if lit != neg]
            new_clauseset.append(new_clause)
        else:
            new_clauseset.append(clause)
    return new_clauseset

def find_one_literal(clauseset):
    for clause in clauseset:
        if len(clause) == 1:
            return clause[0]
    return None

def find_pure_literal(clauseset):
    counts = {}
    for clause in clauseset:
        for literal in clause:
            counts[literal] = counts.get(literal, 0) + 1
    for literal, _ in counts.items():
        if counts.get(-literal, 0) == 0:
            return literal
    return None

def moms(clauseset):
    min_size = float('inf')
    for clause in clauseset:
        if len(clause) < min_size:
            min_size = len(clause)
    
    if min_size == float('inf'):
        return None
    
    var_counts = {}
    for clause in clauseset:
        if len(clause) == min_size:
            for lit in clause:
                var = abs(lit)
                var_counts[var] = var_counts.get(var, 0) + 1
    
    max_var = None
    max_count = -1
    for var, count in var_counts.items():
        if count > max_count:
            max_count = count
            max_var = var
    
    if max_var is not None:
        pos_count = 0
        neg_count = 0
        for clause in clauseset:
            if max_var in clause:
                pos_count += 1
            if -max_var in clause:
                neg_count += 1
        
        return max_var if pos_count >= neg_count else -max_var
    
    return None

def dpll(clauseset):
    global recursive_calls, unit_props
    recursive_calls += 1

    #Check if clause set is empty
    if not clauseset:
        return True

    #Search for empty clause
    for clause in clauseset:
        if not clause:
            return False

    #Unit propagation
    one_literal = find_one_literal(clauseset)
    if one_literal is not None:
        unit_props += 1
        return dpll(propagation(clauseset, one_literal))

    #Pure literal elimination
    pure = find_pure_literal(clauseset)
    if pure is not None:
        return dpll(propagation(clauseset, pure))

    #Branching
    branch_lit = moms(clauseset)
    if branch_lit is None:
        for clause in clauseset:
            if clause:
                branch_lit = clause[0]
                break
    
    if branch_lit is None:
        return True
    
    if dpll(propagation(clauseset, branch_lit)):
        return True
    
    return dpll(propagation(clauseset, -branch_lit))

if __name__ == "__main__":
    filename = sys.argv[1]
    clauseset, num_vars, num_clauses = read_clauseset(filename)
    sat = dpll(clauseset)
    ratio = num_clauses / num_vars if num_vars > 0 else 0
    print(json.dumps({
        "result": "SAT" if sat else "UNSAT",
        "recursive_calls": recursive_calls,
        "unit_props": unit_props,
        "num_vars": num_vars,
        "num_clauses": num_clauses,
        "ratio": ratio
    }))