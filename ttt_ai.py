"""
ttt_ai.py  —  Tic Tac Toe: Minimax AI with Alpha-Beta Pruning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MINIMAX ALGORITHM — EXPLANATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Minimax is a recursive decision-making algorithm used in
 two-player zero-sum games.

 Two players:
   • Maximiser (AI = 'O')  → tries to MAXIMISE the score
   • Minimiser (Human='X') → tries to MINIMISE the score

 The algorithm builds a full game tree from the current
 board state and picks the move that leads to the best
 outcome assuming the opponent also plays perfectly.

 Pseudocode:
 ───────────
   minimax(board, depth, is_maximising):
     if terminal_state:
         return evaluate(board) ± depth_bonus

     if is_maximising:
         best = -infinity
         for each empty cell:
             play AI move
             score = minimax(board, depth+1, False)
             undo move
             best = max(best, score)
         return best
     else:
         best = +infinity
         for each empty cell:
             play Human move
             score = minimax(board, depth+1, True)
             undo move
             best = min(best, score)
         return best

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TIME & SPACE COMPLEXITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Plain Minimax:
   Time  : O(b^d)   b = branching factor (≤9), d = depth (≤9)
           Worst case = 9! = 362,880 leaf nodes
   Space : O(d)     — recursion stack depth

 With Alpha-Beta Pruning:
   Time  : O(b^(d/2)) in best case  ≈ O(√(b^d))
           Reduces 362,880 to ~2,000 nodes explored on avg
   Space : O(d)     — same stack, no extra data structures

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ALPHA-BETA PRUNING — EXPLANATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Two extra parameters:
   alpha = best score the Maximiser can GUARANTEE so far
   beta  = best score the Minimiser can GUARANTEE so far

 Pruning rule:
   • In a Maximiser node: if score ≥ beta  → PRUNE (beta cut-off)
     The Minimiser above already has a better option; this branch
     will never be chosen.
   • In a Minimiser node: if score ≤ alpha → PRUNE (alpha cut-off)
     The Maximiser above already has a better option.

 Result: Branches that cannot influence the final decision
         are never explored → massive speedup.
"""

import math
from ttt_logic import (
    EMPTY, HUMAN, AI,
    evaluate, is_moves_left, get_empty_cells,
    game_over, copy_board
)


# ─────────────────────────────────────────────────────────────────────────────
# Node counter (resets each call to best_move)
# ─────────────────────────────────────────────────────────────────────────────

class _Counter:
    """Simple mutable integer wrapper shared across recursive calls."""
    def __init__(self):
        self.value = 0

    def reset(self):
        self.value = 0

    def inc(self):
        self.value += 1


# ─────────────────────────────────────────────────────────────────────────────
# Core Minimax with Alpha-Beta Pruning
# ─────────────────────────────────────────────────────────────────────────────

def minimax(board: list,
            depth: int,
            is_maximising: bool,
            alpha: float,
            beta: float,
            counter: _Counter) -> int:
    """
    Recursively evaluate the game tree using Minimax + Alpha-Beta Pruning.

    Parameters
    ----------
    board          : current board state (list of 9 cells)
    depth          : recursion depth (0 = root; increases each ply)
    is_maximising  : True  → AI's turn (Maximiser)
                     False → Human's turn (Minimiser)
    alpha          : best guaranteed score for Maximiser (starts at -inf)
    beta           : best guaranteed score for Minimiser (starts at +inf)
    counter        : shared node counter for instrumentation

    Returns
    -------
    int : the minimax score of this board state

    DAA Time  : O(b^d) without pruning, O(b^(d/2)) with pruning
    DAA Space : O(d) recursion stack
    """
    counter.inc()   # count every node visited

    # ── Base case: terminal state ────────────────────────────────────────────
    if game_over(board):
        score = evaluate(board)
        # Depth bonus: prefer winning in fewer moves (score ± depth)
        if score > 0:
            return score - depth    # win sooner  → higher score
        if score < 0:
            return score + depth    # lose later  → smaller penalty (AI delays)
        return 0                    # draw

    # ── Recursive case ───────────────────────────────────────────────────────
    empty_cells = get_empty_cells(board)

    if is_maximising:
        # AI ('O') maximises
        best = -math.inf
        for idx in empty_cells:
            board[idx] = AI                                   # make move
            score = minimax(board, depth + 1, False,
                            alpha, beta, counter)             # recurse
            board[idx] = EMPTY                                # undo move

            best  = max(best, score)
            alpha = max(alpha, best)

            # ── Beta cut-off (Alpha-Beta Pruning) ─────────────────────────────
            # If AI's best ≥ Minimiser's current guarantee,
            # Minimiser would never let this branch be reached → prune.
            if beta <= alpha:
                break   # ← PRUNE: skip remaining siblings

        return best

    else:
        # Human ('X') minimises
        best = +math.inf
        for idx in empty_cells:
            board[idx] = HUMAN                                # make move
            score = minimax(board, depth + 1, True,
                            alpha, beta, counter)             # recurse
            board[idx] = EMPTY                                # undo move

            best = min(best, score)
            beta = min(beta, best)

            # ── Alpha cut-off (Alpha-Beta Pruning) ────────────────────────────
            # If Minimiser's best ≤ Maximiser's current guarantee,
            # Maximiser would never let this branch be reached → prune.
            if beta <= alpha:
                break   # ← PRUNE: skip remaining siblings

        return best


# ─────────────────────────────────────────────────────────────────────────────
# Best move selector (called by the GUI)
# ─────────────────────────────────────────────────────────────────────────────

def best_move(board: list) -> tuple:
    """
    Find the optimal move for the AI using Minimax + Alpha-Beta Pruning.

    Returns
    -------
    (move_index, nodes_explored, score)
        move_index    : board index (0–8) of the best move
        nodes_explored: total minimax nodes evaluated
        score         : minimax value of the chosen move

    DAA Role: This is the entry point for the AI each turn.
              It iterates over all current empty cells, calls minimax
              for each, and picks the move with the highest score.

    Time Complexity: O(b^(d/2)) with alpha-beta  (b≤9, d≤9)
    Space Complexity: O(d) call stack
    """
    counter    = _Counter()
    best_score = -math.inf
    move_idx   = -1

    empty_cells = get_empty_cells(board)

    # Special case: first move on an empty board — always pick centre (4)
    # This is a common opening heuristic; no recursion needed.
    if len(empty_cells) == 9:
        counter.inc()
        return (4, 1, 0)

    for idx in empty_cells:
        board[idx] = AI                     # try AI move
        score = minimax(
            board,
            depth=0,
            is_maximising=False,            # next turn is Human (minimiser)
            alpha=-math.inf,
            beta=+math.inf,
            counter=counter
        )
        board[idx] = EMPTY                  # undo

        if score > best_score:
            best_score = score
            move_idx   = idx

    return (move_idx, counter.value, best_score)


# ─────────────────────────────────────────────────────────────────────────────
# Without pruning — used for comparison demo
# ─────────────────────────────────────────────────────────────────────────────

def minimax_plain(board: list,
                  depth: int,
                  is_maximising: bool,
                  counter: _Counter) -> int:
    """
    Plain Minimax WITHOUT alpha-beta pruning.
    Used to demonstrate the node-count difference.

    Time: O(b^d)  — guaranteed full tree exploration
    """
    counter.inc()

    if game_over(board):
        score = evaluate(board)
        if score > 0: return score - depth
        if score < 0: return score + depth
        return 0

    empty_cells = get_empty_cells(board)

    if is_maximising:
        best = -math.inf
        for idx in empty_cells:
            board[idx] = AI
            score = minimax_plain(board, depth + 1, False, counter)
            board[idx] = EMPTY
            best = max(best, score)
        return best
    else:
        best = +math.inf
        for idx in empty_cells:
            board[idx] = HUMAN
            score = minimax_plain(board, depth + 1, True, counter)
            board[idx] = EMPTY
            best = min(best, score)
        return best


def best_move_plain(board: list) -> tuple:
    """
    Optimal move WITHOUT alpha-beta pruning — for node-count comparison.
    Returns (move_index, nodes_explored, score).
    """
    counter    = _Counter()
    best_score = -math.inf
    move_idx   = -1

    if len(get_empty_cells(board)) == 9:
        counter.inc()
        return (4, 1, 0)

    for idx in get_empty_cells(board):
        board[idx] = AI
        score = minimax_plain(board, 0, False, counter)
        board[idx] = EMPTY
        if score > best_score:
            best_score = score
            move_idx   = idx

    return (move_idx, counter.value, best_score)
