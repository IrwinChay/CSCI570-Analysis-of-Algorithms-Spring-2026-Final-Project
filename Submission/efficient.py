import sys
import time
import psutil

# Constants (hardcoded as required by project description)
DELTA = 30
ALPHA = {
    "A": {"A": 0, "C": 110, "G": 48, "T": 94},
    "C": {"A": 110, "C": 0, "G": 118, "T": 48},
    "G": {"A": 48, "C": 118, "G": 0, "T": 110},
    "T": {"A": 94, "C": 48, "G": 110, "T": 0},
}

# Build string by repeatedly inserting a copy after the given index 
def generate_string(base, indices) -> str:
    s = base
    for i in indices:
        if i < 0 or i >= len(s):
            raise ValueError(f"Index {i} out of range for string of length {len(s)}.")
        s = s[:i + 1] + s + s[i + 1:]
    return s

# Parse input file into two generated strings 
def parse_input(filepath) -> tuple:
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    if len(lines) < 2:
        raise ValueError("Input file must contain two base strings.")
    i = 0
    string1 = lines[i]
    i += 1
    indices1 = []
    while i < len(lines) and lines[i].isdigit():
        indices1.append(int(lines[i]))
        i += 1
    if i >= len(lines):
        raise ValueError("Input file does not contain a second base string.")
    string2 = lines[i]
    i += 1
    indices2 = []
    while i < len(lines) and lines[i].isdigit():
        indices2.append(int(lines[i]))
        i += 1
    return generate_string(string1, indices1), generate_string(string2, indices2)


# Space-efficient forward dynamic programming that returns only the last row of the cost table
# Returns list where row[j] = optimal cost of aligning X with Y[:j] 
# O(len(Y)) space
def alignment_score(X, Y) -> list:
    m = len(X)
    n = len(Y)
    # Base case 
    prev = [i * DELTA for i in range(n + 1)]
    curr = [0] * (n + 1)
    for i in range(m):
        curr[0] = (i + 1) * DELTA
        alpha_row = ALPHA[X[i]]
        for j in range(n):
            # Diagonal: match/mismatch
            match = prev[j] + alpha_row[Y[j]]
            # Up: gap in Y
            delete = prev[j + 1] + DELTA
            # Left: gap in X
            insert = curr[j] + DELTA
            if match <= delete:
                if match <= insert:
                    curr[j + 1] = match
                else:
                    curr[j + 1] = insert
            else:
                if delete <= insert:
                    curr[j + 1] = delete
                else:
                    curr[j + 1] = insert
        prev, curr = curr, prev
    return prev

# Full dynamic programming with backtrack for base cases (m <= 1 or n <= 1)
def dp_alignment(X, Y, res1, res2) -> None:
    m = len(X)
    n = len(Y)

    # Base case
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        dp[i][0] = i * DELTA
    for j in range(1, n + 1):
        dp[0][j] = j * DELTA

    # Fill DP table
    for i in range(1, m + 1):
        alpha_row = ALPHA[X[i - 1]]
        dp_prev = dp[i - 1]
        dp_curr = dp[i]
        for j in range(1, n + 1):
            # Diagonal: match/mismatch
            match = dp_prev[j - 1] + alpha_row[Y[j - 1]]
            # Up: gap in Y
            delete = dp_prev[j] + DELTA
            # Left: gap in X
            insert = dp_curr[j - 1] + DELTA
            if match <= delete:
                if match <= insert:
                    dp_curr[j] = match
                else:
                    dp_curr[j] = insert
            else:
                if delete <= insert:
                    dp_curr[j] = delete
                else:
                    dp_curr[j] = insert

    # Backtrack 
    x_align, y_align = [], []
    i, j = m, n
    while i > 0 and j > 0:
        if dp[i][j] == dp[i - 1][j - 1] + ALPHA[X[i - 1]][Y[j - 1]]:
            # Diagonal
            x_align.append(X[i - 1])
            y_align.append(Y[j - 1])
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + DELTA:
            # Up
            x_align.append(X[i - 1])
            y_align.append('_')
            i -= 1
        else:
            # Left
            x_align.append('_')
            y_align.append(Y[j - 1])
            j -= 1
    while i > 0:
        # Remaining X characters
        x_align.append(X[i - 1])
        y_align.append('_')
        i -= 1
    while j > 0:
        # Remaining Y characters
        x_align.append('_')
        y_align.append(Y[j - 1])
        j -= 1
    x_align.reverse()
    y_align.reverse()
    res1.extend(x_align)
    res2.extend(y_align)

# Space efficient sequence alignment based on Hirschberg's algorithm
# O(mn) time, O(m+n) space
# https://en.wikipedia.org/wiki/Hirschberg%27s_algorithm
def efficient(X, Y, res1, res2) -> None:
    m = len(X)
    n = len(Y)

    # Base cases
    if m == 0:
        for c in Y:
            res1.append('_')
            res2.append(c)
        return
    if n == 0:
        for c in X:
            res1.append(c)
            res2.append('_')
        return
    if m == 1 or n == 1:
        dp_alignment(X, Y, res1, res2)
        return

    # Divide X at midpoint
    mid = m // 2

    # Forward: cost of aligning X[:mid] with Y[:j] for each j
    score_l = alignment_score(X[:mid], Y)

    # Backward: cost of aligning X[mid:] with Y[j:] for each j
    score_r = alignment_score(X[mid:][::-1], Y[::-1])

    # Find optimal split on Y
    best = score_l[0] + score_r[n]
    split = 0
    for j in range(1, n + 1):
        c = score_l[j] + score_r[n - j]
        if c < best:
            best = c
            split = j

    # Conquer
    efficient(X[:mid], Y[:split], res1, res2)
    efficient(X[mid:], Y[split:], res1, res2)

# Compute the total alignment cost from aligned character lists
def alignment_cost(res1, res2) -> int:
    cost = 0
    for c1, c2 in zip(res1, res2):
        if c1 == '_' or c2 == '_':
            cost += DELTA
        else:
            cost += ALPHA[c1][c2]
    return cost

def process_memory() -> float:
    process = psutil.Process()
    return process.memory_info().rss / 1024

# Use the space efficient algorithm to solve sequence alignment and compute total memory 
def solve(X, Y) -> tuple:
    res1, res2 = [], []
    efficient(X, Y, res1, res2)
    memory = process_memory()
    return res1, res2, memory
  
def main() -> None:
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    s1, s2 = parse_input(input_file)

    start_time = time.time()
    res1, res2, memory = solve(s1, s2)
    end_time = time.time()
    time_ms = (end_time - start_time) * 1000

    cost = alignment_cost(res1, res2)

    with open(output_file, 'w') as f:
        f.write(str(cost) + '\n')
        f.write(''.join(res1) + '\n')
        f.write(''.join(res2) + '\n')
        f.write(str(time_ms) + '\n')
        f.write(str(memory) + '\n')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("Input must contain two file paths\n")
        sys.exit(1)
    main()