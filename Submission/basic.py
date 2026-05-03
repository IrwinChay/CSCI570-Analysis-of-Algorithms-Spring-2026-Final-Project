import sys
# from resource import * 
import time
import psutil

DELTA = 30

ALPHA_TABLE = {
    "A": {"A": 0,   "C": 110, "G": 48,  "T": 94},
    "C": {"A": 110, "C": 0,   "G": 118, "T": 48},
    "G": {"A": 48,  "C": 118, "G": 0,   "T": 110},
    "T": {"A": 94,  "C": 48,  "G": 110, "T": 0},
}

def process_memory():
    process = psutil.Process() 
    memory_info = process.memory_info()
    memory_consumed = int(memory_info.rss/1024)
    return memory_consumed


def time_wrapper(s, t): 
    start_time = time.time() 
    cost, s_aligned, t_aligned, memory = sequence_alignment(s, t)
    end_time = time.time()
    time_taken = (end_time - start_time)*1000 
    # print(cost)
    # print("".join(s_aligned))
    # print("".join(t_aligned))
    # print(time_taken)
    # print(memory)
    return cost, s_aligned, t_aligned, time_taken, memory


def generate_strings(f_path):
    s = None
    t = None
    with open(f_path, 'r') as file:
        for line in file:
            l = line.strip()
            if not line:
                continue
            # if the line specifies an index
            if l.isdigit():
                # raise error if first base string doesn't exist
                if s is None:
                    raise ValueError("First line does not contain valid string.")
                idx = int(l)
                # insert using given index
                if t is None:
                    if idx < 0 or idx >= len(s):
                        raise ValueError(f"Index {idx} out of length for s.")
                    else:
                        s = s[:idx + 1] + s + s[idx + 1:]
                else:
                    if idx < 0 or idx >= len(t):
                        raise ValueError(f"Index {idx} out of length for t.")
                    else:
                        t = t[:idx + 1] + t + t[idx + 1:]
            # if the line is a base string
            else:
                if s is None:
                    s = l
                elif t is None:
                    t = l
                else:
                    raise ValueError("File contains more than two base strings.")
        # raise error if s or t cannot be constructed
        if s is None or t is None:
            raise ValueError("File does not contain two base strings.")
        return s, t


def sequence_alignment(s, t):
    start_memory = process_memory()
    M = [[0 for _ in range(len(t) + 1)] for _ in range(len(s) + 1)]
    # base cases where one string is empty
    for i in range(1, len(s) + 1):
        M[i][0] = i * DELTA
    for j in range(1, len(t) + 1):
        M[0][j] = j * DELTA
    # bottom up pass
    for i in range(1, len(s) + 1):
        for j in range(1, len(t) + 1):
            M[i][j] = min(
                M[i - 1][j - 1] + ALPHA_TABLE[s[i - 1]][t[j - 1]],
                M[i - 1][j] + DELTA,
                M[i][j - 1] + DELTA,
            )
    # top down pass for alignment
    s_aligned = []
    t_aligned = []
    i = len(s)
    j = len(t)
    while i > 0 or j > 0:
        # s[i-1] aligned with a gap
        if i > 0 and M[i][j] == M[i - 1][j] + DELTA:
            s_aligned.append(s[i - 1])
            t_aligned.append("_")
            i -= 1
            continue
        # t[j-1] aligned with a gap
        if j > 0 and M[i][j] == M[i][j - 1] + DELTA:
            s_aligned.append("_")
            t_aligned.append(t[j - 1])
            j -= 1
            continue
        # s[i-1] aligned with t[j-1]
        if i > 0 and j > 0:
            if M[i][j] == M[i - 1][j - 1] + ALPHA_TABLE[s[i - 1]][t[j - 1]]:
                s_aligned.append(s[i - 1])
                t_aligned.append(t[j - 1])
                i -= 1
                j -= 1
                continue
    s_aligned.reverse()
    t_aligned.reverse()
    end_memory = process_memory()
    return M[len(s)][len(t)], "".join(s_aligned), "".join(t_aligned), end_memory-start_memory

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Two file paths expected: python3 basic.py <path to input file> <path to output file>")
        sys.exit(1)
    
    in_path = sys.argv[1]
    out_path = sys.argv[2]

    try:
        s, t = generate_strings(in_path)
        # print(s, len(s))
        # print(t, len(t))
        cost, s_aligned, t_aligned, time_taken, memory = time_wrapper(s, t)
        with open(out_path, "w") as file:
            file.write(str(cost) + "\n")
            file.write(s_aligned + "\n")
            file.write(t_aligned + "\n")
            file.write(str(time_taken)  + "\n")
            file.write(str(memory))
    except Exception as e:
        print(e)
        sys.exit(1)
