import sys
import time
import json

TIME_LIMIT = 600
START_TIME = None
resolution_steps = 0
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


def resolution(clauseset):
    global resolution_steps
    MAX_RESOLVENT_SIZE = 10
    
    cs = set(frozenset(clause) for clause in clauseset)
    new = set()
    cs_list = list(cs)
    
    while True:
        if time.time() - START_TIME > TIME_LIMIT:
            ratio = num_clauses / num_vars if num_vars > 0 else 0
            print(json.dumps({
                "result": "UNKNOWN",
                "timeout": True,
                "resolution_steps": resolution_steps,
                "recursive_calls": recursive_calls,
                "unit_props": unit_props,
                "num_vars": num_vars,
                "num_clauses": num_clauses,
                "ratio": ratio
            }))
            sys.exit(1)
            
        for i in range(len(cs_list)):
            for j in range(i+1, len(cs_list)):
                clause1 = cs_list[i]
                clause2 = cs_list[j]                
                if len(clause1) + len(clause2) - 2 > MAX_RESOLVENT_SIZE:
                    continue                    
                for lit in clause1:
                    if -lit in clause2:
                        resolvent = (clause1 - {lit}) | (clause2 - {-lit})
                        if len(resolvent) > MAX_RESOLVENT_SIZE:
                            continue
                        resolution_steps += 1
                        if not resolvent:
                            return False
                        new_fs = frozenset(resolvent)
                        if new_fs not in cs:
                            new.add(new_fs)
        if not new:
            return True
        for fs in new:
            cs.add(fs)
            cs_list.append(fs)
        new.clear()


if __name__ == "__main__":
    START_TIME = time.time()
    filename = sys.argv[1]
    clauseset, num_vars, num_clauses = read_clauseset(filename)
    sat = resolution(clauseset)
    ratio = num_clauses / num_vars if num_vars > 0 else 0
    print(json.dumps({
        "result": "SAT" if sat else "UNSAT",
        "resolution_steps": resolution_steps,
        "recursive_calls": recursive_calls,
        "unit_props": unit_props,
        "num_vars": num_vars,
        "num_clauses": num_clauses,
        "ratio": ratio
    }))