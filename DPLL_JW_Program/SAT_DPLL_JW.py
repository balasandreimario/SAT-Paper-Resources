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

def jw(clauseset):
    jw_score = {}
    for clause in clauseset:
        weight = 2.0 ** (-len(clause))
        for lit in clause:
            jw_score[lit] = jw_score.get(lit, 0) + weight
    
    if not jw_score:
        return None
    
    max_lit = max(jw_score, key=jw_score.get)
    
    return max_lit

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
    if one_literal:
        unit_props += 1
        return dpll(propagation(clauseset, one_literal))

    #Pure literal elimination
    pure = find_pure_literal(clauseset)
    if pure:
        return dpll(propagation(clauseset, pure))

    #Branching
    branch_lit = jw(clauseset)
    
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