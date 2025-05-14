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


def choose_variable(clauseset):
    for clause in clauseset:
        if clause:
            return abs(clause[0])
    return None

def is_tautology(merged_clause):
    for lit in merged_clause:
        if -lit in merged_clause:
            return True
    return False

def dp(clauseset, vars_list):
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
    if one_literal:
        unit_props += 1
        new_clauseset = propagation(clauseset, one_literal)
        new_vars = [v for v in vars_list if v != abs(one_literal)]
        return dp(new_clauseset, new_vars)

    #Pure literal
    pure = find_pure_literal(clauseset)
    if pure:
        new_clauseset = propagation(clauseset, pure)
        new_vars = [v for v in vars_list if v != abs(pure)]
        return dp(new_clauseset, new_vars)

    #Resolution rule
    var = choose_variable(clauseset)
    if var is None:
        return True
        
    positive = [c for c in clauseset if var in c]
    negative = [c for c in clauseset if -var in c]
    tup_resolvents = []
    resolvents = []    
    max_resolvent_size = 100
    
    for c1 in positive:
        for c2 in negative:
            if len(c1) + len(c2) - 2 > max_resolvent_size:
                continue
                
            merged = []
            for lit in c1:
                if lit != var and lit not in merged:
                    merged.append(lit)
            for lit in c2:
                if lit != -var and lit not in merged:
                    merged.append(lit)
            
            if not merged:
                return False
                
            if is_tautology(merged):
                continue
                
            merged_canonical = tuple(sorted(merged))
            if merged_canonical not in tup_resolvents:
                tup_resolvents.append(merged_canonical)
                resolvents.append(merged)
    
    reduced = [c for c in clauseset if var not in c and -var not in c]
    
    reduced_tup = [tuple(sorted(c)) for c in reduced]
    
    for i, r in enumerate(resolvents):
        r_tup = tup_resolvents[i]
        if r_tup not in reduced_tup:
            reduced.append(r)
            reduced_tup.append(r_tup)
            
    return dp(reduced, [v for v in vars_list if v != var])

if __name__ == '__main__':
    filename = sys.argv[1]
    
    clauseset, num_vars, num_clauses = read_clauseset(filename)
    max_var = 0
    for clause in clauseset:
        for lit in clause:
            max_var = max(max_var, abs(lit))
    
    vars_list = list(range(1, max_var + 1))
    
    sat = dp(clauseset, vars_list)
    
    ratio = num_clauses / num_vars if num_vars > 0 else 0
    print(json.dumps({
        "result": "SAT" if sat else "UNSAT",
        "recursive_calls": recursive_calls,
        "unit_props": unit_props,
        "num_vars": num_vars,
        "num_clauses": num_clauses,
        "ratio": ratio
    }))