import subprocess, json, csv, glob, os, sys, time
import psutil # type: ignore
#"type: ignore" is included because my text editor had some issue with detecting psutil being installed for some reason, the program is fully operational (if psutil is installed)

TIMEOUT = 600
REPEATS = 1

def run_solver(cmd):
    start = time.perf_counter()
    proc = psutil.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    pid = proc.pid
    peak_mem = 0
    
    def get_memory():
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            
            if hasattr(memory_info, 'peak_wset'):
                return memory_info.peak_wset
            elif hasattr(memory_info, 'peak_working_set_size'):
                return memory_info.peak_working_set_size
            else:
                return memory_info.rss
        except:
            return 0
    
    monitoring_timeout = False
    
    while proc.poll() is None:
        elapsed = time.perf_counter() - start
        if elapsed > TIMEOUT:
            proc.kill()
            monitoring_timeout = True
            break    
        mem = get_memory()
        peak_mem = max(peak_mem, mem)
        time.sleep(0.1)

    try:
        stdout, stderr = proc.communicate(timeout=max(0.1, TIMEOUT - (time.perf_counter() - start)))
        timed_out = monitoring_timeout
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        timed_out = True
    
    end = time.perf_counter()
    elapsed = end - start
    
    return stdout, stderr, elapsed, peak_mem, timed_out

def json_output(stdout):
    try:
        return json.loads(stdout)
    except:
        return {}

if __name__ == "__main__":
    cnf_dir = sys.argv[1]
    solvers = [
        ("dpll",       ["python", "DPLL_Program\SAT_DPLL.py"]),
        ("dpll_moms",  ["python", "DPLL_MOMS_Program\SAT_DPLL_MOMS.py"]),
        ("dpll_jw",    ["python", "DPLL_JW_Program\SAT_DPLL_JW.py"]),
        ("dp",         ["python", "DP_Program\SAT_DP.py"]),
        ("resolution", ["python", "Resolution_Program\SAT_Resolution.py"])
    ]

    cnf_paths = sorted(glob.glob(os.path.join(cnf_dir, "*.cnf")))
    output_file = "results.csv"
    fieldnames = [
        "solver", "instance", "run",
        "time_s", "mem_bytes", "timed_out",
        "result", "resolution_steps", "recursive_calls", "unit_props",
        "num_vars", "num_clauses", "ratio"
    ]

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for cnf in cnf_paths:
            basename = os.path.basename(cnf)
            for solver_name, base_cmd in solvers:
                for run_id in range(1, REPEATS + 1):
                    cmd = base_cmd + [cnf]
                    print(f"Running: {' '.join(cmd)}")
                    stdout, stderr, elapsed, mem, timed_out = run_solver(cmd)
                    counters = json_output(stdout)
                    row = {
                        "solver": solver_name,
                        "instance": basename,
                        "run": run_id,
                        "time_s": round(elapsed, 4),
                        "mem_bytes": mem,
                        "timed_out": timed_out,
                        **counters
                    }
                    writer.writerow(row)
                    print(f"[{solver_name}] {basename} run {run_id}: time={elapsed:.2f}s mem={mem//1024//1024}MB{' T/O' if timed_out else ''}")