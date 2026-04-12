"""
ttt_logic.py  —  Tic Tac Toe: Board & Game Logic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAA Concept: Pure game-state management layer.
Separated from AI and UI so each module has a single responsibility.

Board representation
────────────────────
  A 3×3 grid stored as a flat Python list of 9 cells.
  Index mapping:
      0 | 1 | 2
     ───┼───┼───
      3 | 4 | 5
     ───┼───┼───
      6 | 7 | 8

  Each cell holds one of three values:
      EMPTY  = ''
      HUMAN  = 'X'
      AI     = 'O'
"""

# ─── Symbols ──────────────────────────────────────────────────────────────────
EMPTY = ''
HUMAN = 'X'
AI    = 'O'

# ─── All 8 winning lines (rows, cols, diagonals) ──────────────────────────────
WIN_LINES = [
    (0, 1, 2),   # top row
    (3, 4, 5),   # mid row
    (6, 7, 8),   # bot row
    (0, 3, 6),   # left col
    (1, 4, 7),   # mid col
    (2, 5, 8),   # right col
    (0, 4, 8),   # diagonal \
    (2, 4, 6),   # diagonal /
]


# ─────────────────────────────────────────────────────────────────────────────
# Board factory
# ─────────────────────────────────────────────────────────────────────────────

def new_board() -> list:
    """Return a fresh, empty 3×3 board.  Time: O(1), Space: O(1)."""
    return [EMPTY] * 9


def copy_board(board: list) -> list:
    """Return a shallow copy of the board. Time: O(9)=O(1)."""
    return board[:]


# ─────────────────────────────────────────────────────────────────────────────
# Move queries
# ─────────────────────────────────────────────────────────────────────────────

def is_moves_left(board: list) -> bool:
    """
    Check whether any empty cell remains.

    DAA Role: Base-case guard for the Minimax recursion tree.
              If no moves are left and nobody won → draw.

    Time Complexity: O(n) where n = 9 (constant)
    """
    return EMPTY in board


def get_empty_cells(board: list) -> list:
    """
    Return indices of all empty cells.

    Used by Minimax to enumerate possible moves at each node.
    Time: O(9) = O(1)
    """
    return [i for i, cell in enumerate(board) if cell == EMPTY]


# ─────────────────────────────────────────────────────────────────────────────
# Win / draw detection
# ─────────────────────────────────────────────────────────────────────────────

def check_winner(board: list) -> str:
    """
    Check all 8 winning lines.

    Returns
    -------
    'X'   if Human wins
    'O'   if AI wins
    ''    otherwise (no winner yet)

    Time Complexity: O(8 × 3) = O(1)  — constant, board is fixed size
    """
    for a, b, c in WIN_LINES:
        if board[a] == board[b] == board[c] and board[a] != EMPTY:
            return board[a]      # winner's symbol
    return EMPTY


def get_winning_line(board: list):
    """
    Return the (a, b, c) triple of the winning line, or None.
    Used by the GUI to highlight winning cells.
    """
    for a, b, c in WIN_LINES:
        if board[a] == board[b] == board[c] and board[a] != EMPTY:
            return (a, b, c)
    return None


def is_draw(board: list) -> bool:
    """
    Draw  ⟺  no winner AND no empty cells.
    Time: O(1)
    """
    return (not is_moves_left(board)) and check_winner(board) == EMPTY


def game_over(board: list) -> bool:
    """
    Terminal state check used by Minimax.
    True if someone won OR the board is full.
    """
    return check_winner(board) != EMPTY or not is_moves_left(board)


# ─────────────────────────────────────────────────────────────────────────────
# Score / evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(board: list) -> int:
    """
    Static evaluation function — the 'heuristic' at a terminal node.

    DAA Role: Assigns a numeric score to a terminal board state so
              Minimax can compare branches numerically.

    Scoring
    -------
      +10   AI  ('O') wins
      -10   Human ('X') wins
        0   Draw

    The depth is subtracted/added from the score so the AI prefers
    wins in fewer moves (handled in minimax, not here).

    Time Complexity: O(1) — delegates to check_winner (constant)
    """
    winner = check_winner(board)
    if winner == AI:
        return +10
    if winner == HUMAN:
        return -10
    return 0          # draw or in-progress


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-print (debug helper)
# ─────────────────────────────────────────────────────────────────────────────

def print_board(board: list):
    """Print board to console for debugging."""
    symbols = [c if c != EMPTY else '.' for c in board]
    print(f"\n {symbols[0]} | {symbols[1]} | {symbols[2]}")
    print(f"---+---+---")
    print(f" {symbols[3]} | {symbols[4]} | {symbols[5]}")
    print(f"---+---+---")
    print(f" {symbols[6]} | {symbols[7]} | {symbols[8]}\n")
