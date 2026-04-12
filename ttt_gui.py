"""
ttt_gui.py  —  Tic Tac Toe: Tkinter GUI (Entry Point)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this file to play:
    python ttt_gui.py

Features
────────
  • Dark neon-themed UI (deep space look)
  • Animated X / O drawing (stepping reveal)
  • Win-line highlight (animated glow)
  • Live stats panel: nodes explored, AI score, depth
  • Alpha-Beta vs Plain Minimax node comparison
  • 700 ms AI thinking delay (natural feel)
  • Responsive restart, difficulty toggle
  • Hover effects on empty cells
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import math

from ttt_logic  import (new_board, copy_board, check_winner,
                         get_winning_line, is_draw, game_over,
                         EMPTY, HUMAN, AI)
from ttt_ai     import best_move, best_move_plain


# ─────────────────────────────────────────────────────────────────────────────
# Colour Palette
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg"          : "#0a0c1c",          # window background
    "panel"       : "#0f1228",          # side panel background
    "grid_bg"     : "#0d1025",          # grid background
    "line"        : "#1e2244",          # grid lines
    "cell_idle"   : "#0f1228",          # empty cell fill
    "cell_hover"  : "#1a1e3c",          # hover fill
    "x_color"     : "#ff4f88",          # human X — hot pink
    "o_color"     : "#00e5cc",          # AI   O — electric cyan
    "win_glow"    : "#ffd700",          # golden winning glow
    "text_head"   : "#ffffff",
    "text_body"   : "#9095c0",
    "text_accent" : "#ffc800",
    "btn_restart" : "#1e2244",
    "btn_hover"   : "#2a3066",
    "status_win"  : "#ffd700",
    "status_draw" : "#9095c0",
    "status_turn" : "#00e5cc",
}

# ─────────────────────────────────────────────────────────────────────────────
# Sizes
# ─────────────────────────────────────────────────────────────────────────────
CELL_SIZE   = 160          # pixels per cell
GRID_PAD    = 12           # padding inside each cell
LINE_W      = 4            # grid line width (px)
SYMBOL_W    = 8            # stroke width for X/O drawing
ANIM_STEPS  = 18           # animation frames for symbol reveal
ANIM_MS     = 12           # ms per animation frame (~83 fps)
AI_DELAY_MS = 700          # delay before AI moves (ms)
WIN_GLOW_MS = 60           # glow pulse interval (ms)


# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────

class TicTacToeApp(tk.Tk):
    """
    Main Tkinter application window.

    Architecture
    ────────────
    This class owns the root window.  All UI composition and
    game-state management happens here.  The AI logic lives purely
    in ttt_ai.py (no GUI code crosses over).
    """

    def __init__(self):
        super().__init__()

        self.title("Tic Tac Toe — Minimax AI  |  DAA Project")
        self.resizable(False, False)
        self.configure(bg=C["bg"])

        # ── Fonts ─────────────────────────────────────────────────────────────
        try:
            self.fnt_title  = tkfont.Font(family="Consolas", size=18, weight="bold")
            self.fnt_sub    = tkfont.Font(family="Consolas", size=11)
            self.fnt_status = tkfont.Font(family="Consolas", size=14, weight="bold")
            self.fnt_stat   = tkfont.Font(family="Consolas", size=10)
            self.fnt_btn    = tkfont.Font(family="Consolas", size=12, weight="bold")
        except Exception:
            self.fnt_title = self.fnt_sub = self.fnt_status = \
                self.fnt_stat = self.fnt_btn = ("TkFixedFont", 12)

        # ── Game state ────────────────────────────────────────────────────────
        self.board        = new_board()
        self.human_turn   = True   # whose turn it is RIGHT NOW during a game
        self._first_human = True   # preference: does Human go first each game?
        self.game_active  = True
        self.ai_thinking  = False
        self.scores       = {"X": 0, "O": 0, "Draw": 0}

        # ── Stats vars ────────────────────────────────────────────────────────
        self._nodes_ab    = tk.StringVar(value="—")
        self._nodes_plain = tk.StringVar(value="—")
        self._ai_score    = tk.StringVar(value="—")
        self._best_move   = tk.StringVar(value="—")
        self._status_var  = tk.StringVar(value="Your turn  ( X )")
        self._score_var   = tk.StringVar(value="X: 0     O: 0     Draw: 0")

        # ── Win animation state ───────────────────────────────────────────────
        self._win_cells     = []     # indices of winning 3 cells
        self._glow_on       = False
        self._glow_job      = None
        self._glow_active   = False  # guard so old callbacks never fire

        # ── Game-over overlay reference ───────────────────────────────────────
        self._overlay_frame = None   # tk.Frame placed over canvas on game end

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()
        self._refresh_cells()

    # ─────────────────────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        """Assemble the full window layout."""
        outer = tk.Frame(self, bg=C["bg"], padx=20, pady=16)
        outer.pack()

        # ── Title ─────────────────────────────────────────────────────────────
        title_frame = tk.Frame(outer, bg=C["bg"])
        title_frame.pack(fill="x", pady=(0, 12))

        tk.Label(title_frame, text="TIC  TAC  TOE",
                 font=self.fnt_title, bg=C["bg"], fg=C["text_head"]).pack()
        tk.Label(title_frame, text="Minimax AI  ·  Alpha-Beta Pruning  ·  DAA",
                 font=self.fnt_sub, bg=C["bg"], fg=C["text_body"]).pack()

        # ── Score bar ─────────────────────────────────────────────────────────
        tk.Label(outer, textvariable=self._score_var,
                 font=self.fnt_stat, bg=C["bg"], fg=C["text_accent"]).pack()

        sep = tk.Frame(outer, height=1, bg=C["line"])
        sep.pack(fill="x", pady=8)

        # ── Body: grid + stats panel ──────────────────────────────────────────
        body = tk.Frame(outer, bg=C["bg"])
        body.pack()

        self._build_grid(body)
        self._build_stats_panel(body)

        sep2 = tk.Frame(outer, height=1, bg=C["line"])
        sep2.pack(fill="x", pady=8)

        # ── Status + controls ─────────────────────────────────────────────────
        self._build_controls(outer)

    def _build_grid(self, parent):
        """Create the 3×3 canvas grid."""
        TOTAL = CELL_SIZE * 3 + LINE_W * 2
        frame = tk.Frame(parent, bg=C["bg"])
        frame.pack(side="left", padx=(0, 20))

        # Draw grid on a Canvas (allows fine-grained drawing)
        self.canvas = tk.Canvas(
            frame,
            width=TOTAL, height=TOTAL,
            bg=C["grid_bg"],
            highlightthickness=3,
            highlightbackground=C["line"],
            cursor="hand2"
        )
        self.canvas.pack()

        # ── Draw the 4 grid lines ──────────────────────────────────────────────
        for i in range(1, 3):
            x = i * CELL_SIZE + (i - 1) * LINE_W
            self.canvas.create_line(x, 0, x, TOTAL,
                                    fill=C["line"], width=LINE_W, tags="gridline")
            y = x
            self.canvas.create_line(0, y, TOTAL, y,
                                    fill=C["line"], width=LINE_W, tags="gridline")

        # ── Create 9 cell regions + bind events ───────────────────────────────
        self.cell_rects  = []   # background rectangle canvas IDs
        self.cell_items  = []   # list of lists of drawn symbol item IDs

        for idx in range(9):
            row, col = divmod(idx, 3)
            x1 = col * (CELL_SIZE + LINE_W)
            y1 = row * (CELL_SIZE + LINE_W)
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE

            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=C["cell_idle"], outline="",
                tags=f"cell{idx}"
            )
            self.cell_rects.append(rect_id)
            self.cell_items.append([])   # no symbol drawn yet

            # ── Bind events ───────────────────────────────────────────────────
            tag = f"cell{idx}"
            self.canvas.tag_bind(tag, "<Button-1>",
                                  lambda e, i=idx: self._on_cell_click(i))
            self.canvas.tag_bind(tag, "<Enter>",
                                  lambda e, i=idx: self._on_hover(i, True))
            self.canvas.tag_bind(tag, "<Leave>",
                                  lambda e, i=idx: self._on_hover(i, False))

    def _build_stats_panel(self, parent):
        """Right-side stats panel."""
        panel = tk.Frame(parent, bg=C["panel"],
                         relief="flat", bd=0,
                         padx=18, pady=14)
        panel.pack(side="left", fill="y")

        def section(title):
            tk.Label(panel, text=title,
                     font=self.fnt_stat, bg=C["panel"],
                     fg=C["text_accent"]).pack(anchor="w", pady=(10, 0))
            tk.Frame(panel, height=1, bg=C["line"]).pack(fill="x", pady=2)

        def stat_row(label, var):
            row = tk.Frame(panel, bg=C["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=self.fnt_stat,
                     bg=C["panel"], fg=C["text_body"],
                     width=16, anchor="w").pack(side="left")
            tk.Label(row, textvariable=var, font=self.fnt_stat,
                     bg=C["panel"], fg=C["text_head"],
                     anchor="e").pack(side="right")

        # Title
        tk.Label(panel, text="ALGORITHM  STATS",
                 font=self.fnt_btn, bg=C["panel"],
                 fg=C["text_head"]).pack(anchor="w")
        tk.Frame(panel, height=2, bg=C["o_color"]).pack(fill="x", pady=4)

        section("LAST AI MOVE")
        stat_row("Best cell (0-8):", self._best_move)
        stat_row("Minimax score :", self._ai_score)

        section("NODES EXPLORED")
        stat_row("With α-β pruning:", self._nodes_ab)
        stat_row("Without pruning :", self._nodes_plain)

        # Savings label
        self._savings_var = tk.StringVar(value="")
        tk.Label(panel, textvariable=self._savings_var,
                 font=self.fnt_stat, bg=C["panel"],
                 fg=C["text_accent"]).pack(anchor="w", pady=(4, 0))

        # ── Legend ────────────────────────────────────────────────────────────
        section("LEGEND")
        leg_data = [
            (C["x_color"],  "You   (X) — Human"),
            (C["o_color"],  "AI    (O) — Minimax"),
            (C["win_glow"], "Winning line"),
        ]
        for color, label in leg_data:
            row = tk.Frame(panel, bg=C["panel"])
            row.pack(fill="x", pady=2)
            tk.Canvas(row, width=14, height=14,
                      bg=C["panel"], highlightthickness=0).pack(side="left", padx=(0, 6))
            # coloured dot
            dot_c = tk.Canvas(row, width=14, height=14,
                              bg=C["panel"], highlightthickness=0)
            dot_c.pack(side="left", padx=(0, 6))
            dot_c.create_oval(2, 2, 12, 12, fill=color, outline="")
            tk.Label(row, text=label, font=self.fnt_stat,
                     bg=C["panel"], fg=C["text_body"]).pack(side="left")

        # ── Complexity box ────────────────────────────────────────────────────
        section("COMPLEXITY")
        complexity_lines = [
            "Minimax : O(b^d)",
            "b=9, d=9  → 362880",
            "α-β Best : O(b^d/2)",
            "Stack depth : O(d)",
        ]
        for line in complexity_lines:
            tk.Label(panel, text=line, font=self.fnt_stat,
                     bg=C["panel"], fg=C["text_body"],
                     anchor="w").pack(fill="x")

    def _build_controls(self, parent):
        """Status label + buttons row."""
        ctrl = tk.Frame(parent, bg=C["bg"])
        ctrl.pack(fill="x")

        # Status
        self._status_lbl = tk.Label(ctrl, textvariable=self._status_var,
                 font=self.fnt_status, bg=C["bg"],
                 fg=C["status_turn"])
        self._status_lbl.pack(pady=(0, 10))

        # Buttons row
        btn_row = tk.Frame(ctrl, bg=C["bg"])
        btn_row.pack()

        self._make_button(btn_row, "↺  New Game", self._restart, C["o_color"])
        self._make_button(btn_row, "X First / O First", self._toggle_first, C["x_color"])

        # First-player indicator
        self._first_var = tk.StringVar(value="Human (X) plays first")
        tk.Label(ctrl, textvariable=self._first_var,
                 font=self.fnt_stat, bg=C["bg"],
                 fg=C["text_body"]).pack(pady=(6, 0))

        # Keyboard shortcut hint
        self.bind("<r>", lambda e: self._restart())
        self.bind("<R>", lambda e: self._restart())

    def _make_button(self, parent, text, command, accent):
        btn = tk.Label(parent, text=text,
                       font=self.fnt_btn, bg=C["btn_restart"],
                       fg=accent, padx=18, pady=8,
                       cursor="hand2", relief="flat")
        btn.pack(side="left", padx=8)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>",    lambda e: btn.config(bg=C["btn_hover"]))
        btn.bind("<Leave>",    lambda e: btn.config(bg=C["btn_restart"]))
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # Cell Rendering
    # ─────────────────────────────────────────────────────────────────────────

    def _cell_coords(self, idx: int) -> tuple:
        """Return (x1, y1, x2, y2) pixel bounds for cell idx."""
        row, col = divmod(idx, 3)
        x1 = col * (CELL_SIZE + LINE_W)
        y1 = row * (CELL_SIZE + LINE_W)
        return x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE

    def _cell_center(self, idx: int) -> tuple:
        x1, y1, x2, y2 = self._cell_coords(idx)
        return (x1 + x2) // 2, (y1 + y2) // 2

    def _clear_cell_items(self, idx: int):
        for item in self.cell_items[idx]:
            self.canvas.delete(item)
        self.cell_items[idx] = []

    def _refresh_cells(self):
        """Redraw all 9 cells from self.board without animation."""
        for idx in range(9):
            self._clear_cell_items(idx)
            val = self.board[idx]
            if val == HUMAN:
                self._draw_x(idx, animate=False)
            elif val == AI:
                self._draw_o(idx, animate=False)

    def _draw_x(self, idx: int, animate: bool = True):
        """
        Draw the X symbol as two diagonal lines.
        If animate=True, reveal the lines progressively.
        """
        x1, y1, x2, y2 = self._cell_coords(idx)
        pad = GRID_PAD + 20
        ax1, ay1 = x1 + pad, y1 + pad
        ax2, ay2 = x2 - pad, y2 - pad
        bx1, by1 = x2 - pad, y1 + pad
        bx2, by2 = x1 + pad, y2 - pad

        color = C["x_color"]

        if not animate:
            id1 = self.canvas.create_line(ax1, ay1, ax2, ay2,
                                          fill=color, width=SYMBOL_W,
                                          capstyle="round")
            id2 = self.canvas.create_line(bx1, by1, bx2, by2,
                                          fill=color, width=SYMBOL_W,
                                          capstyle="round")
            self.cell_items[idx].extend([id1, id2])
            return

        # Animate: draw line 1 progressively, then line 2
        id1 = self.canvas.create_line(ax1, ay1, ax1, ay1,
                                      fill=color, width=SYMBOL_W, capstyle="round")
        id2 = self.canvas.create_line(bx1, by1, bx1, by1,
                                      fill=color, width=SYMBOL_W, capstyle="round")
        self.cell_items[idx].extend([id1, id2])

        def step_anim(s):
            if s > ANIM_STEPS:
                return
            t = s / ANIM_STEPS
            # Line 1
            ex1 = ax1 + (ax2 - ax1) * t
            ey1 = ay1 + (ay2 - ay1) * t
            self.canvas.coords(id1, ax1, ay1, ex1, ey1)
            # Line 2
            ex2 = bx1 + (bx2 - bx1) * t
            ey2 = by1 + (by2 - by1) * t
            self.canvas.coords(id2, bx1, by1, ex2, ey2)
            self.after(ANIM_MS, step_anim, s + 1)

        step_anim(0)

    def _draw_o(self, idx: int, animate: bool = True):
        """
        Draw the O symbol as an arc that sweeps from 0° to 360°.
        If animate=True, reveal the arc progressively.
        """
        x1, y1, x2, y2 = self._cell_coords(idx)
        pad = GRID_PAD + 18
        color = C["o_color"]

        if not animate:
            oid = self.canvas.create_oval(
                x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                outline=color, width=SYMBOL_W, fill=""
            )
            self.cell_items[idx].append(oid)
            return

        # Animate using arc (extent grows from 0 to 359)
        arc_id = self.canvas.create_arc(
            x1 + pad, y1 + pad, x2 - pad, y2 - pad,
            start=90, extent=0,
            outline=color, width=SYMBOL_W,
            style="arc"
        )
        self.cell_items[idx].append(arc_id)

        def step_anim(s):
            if s > ANIM_STEPS:
                # Replace arc with full oval for crisp rendering
                self.canvas.delete(arc_id)
                oid = self.canvas.create_oval(
                    x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                    outline=color, width=SYMBOL_W, fill=""
                )
                self.cell_items[idx].append(oid)
                return
            extent = -int(360 * s / ANIM_STEPS)
            self.canvas.itemconfig(arc_id, extent=extent)
            self.after(ANIM_MS, step_anim, s + 1)

        step_anim(0)

    # ─────────────────────────────────────────────────────────────────────────
    # Hover Effects
    # ─────────────────────────────────────────────────────────────────────────

    def _on_hover(self, idx: int, entering: bool):
        if self.board[idx] != EMPTY or not self.game_active or self.ai_thinking:
            return
        if not self.human_turn:
            return
        color = C["cell_hover"] if entering else C["cell_idle"]
        self.canvas.itemconfig(self.cell_rects[idx], fill=color)

    # ─────────────────────────────────────────────────────────────────────────
    # Click Handler
    # ─────────────────────────────────────────────────────────────────────────

    def _on_cell_click(self, idx: int):
        """
        Process a human click on cell `idx`.

        Guard conditions:
          • Game must be active
          • It must be human's turn
          • Cell must be empty
          • AI must not currently be computing
        """
        if not self.game_active:
            return
        if not self.human_turn:
            return
        if self.board[idx] != EMPTY:
            return
        if self.ai_thinking:
            return

        # ── Make Human move ───────────────────────────────────────────────────
        self.board[idx] = HUMAN
        self._draw_x(idx, animate=True)
        self.canvas.itemconfig(self.cell_rects[idx], fill=C["cell_idle"])

        # ── Check result ──────────────────────────────────────────────────────
        if self._check_and_handle_result():
            return

        # ── AI's turn ─────────────────────────────────────────────────────────
        self.human_turn = False
        self._set_status("AI is thinking…", C["o_color"])
        self.ai_thinking = True

        # Run AI in background thread so UI stays responsive
        threading.Thread(target=self._ai_move_thread, daemon=True).start()

    # ─────────────────────────────────────────────────────────────────────────
    # AI Move (runs in background thread)
    # ─────────────────────────────────────────────────────────────────────────

    def _ai_move_thread(self):
        """
        Background thread that computes the AI move.
        Tkinter is NOT thread-safe; all UI updates go through self.after().
        """
        time.sleep(AI_DELAY_MS / 1000.0)   # natural "thinking" pause

        # ── Compute best move with Alpha-Beta ─────────────────────────────────
        board_copy = copy_board(self.board)
        move_idx, nodes_ab, score = best_move(board_copy)

        # ── Also compute plain minimax node count for comparison ──────────────
        board_copy2 = copy_board(self.board)
        _, nodes_plain, _ = best_move_plain(board_copy2)

        # ── Schedule GUI update on main thread ───────────────────────────────
        self.after(0, self._apply_ai_move,
                   move_idx, nodes_ab, nodes_plain, score)

    def _apply_ai_move(self, move_idx: int,
                       nodes_ab: int, nodes_plain: int, score: int):
        """Apply the AI's chosen move and update UI. Runs on main thread."""
        self.ai_thinking = False

        if move_idx == -1 or not self.game_active:
            return

        # ── Update stats panel ────────────────────────────────────────────────
        self._nodes_ab.set(f"{nodes_ab:,}")
        self._nodes_plain.set(f"{nodes_plain:,}")
        self._ai_score.set(str(score))
        self._best_move.set(f"Cell {move_idx}  (row {move_idx//3}, col {move_idx%3})")

        # Savings %
        if nodes_plain > 0:
            saved = 100 * (1 - nodes_ab / nodes_plain)
            self._savings_var.set(f"  Pruning saved {saved:.0f}% of nodes!")
        else:
            self._savings_var.set("")

        # ── Make AI move ──────────────────────────────────────────────────────
        self.board[move_idx] = AI
        self._draw_o(move_idx, animate=True)

        # ── Check result ──────────────────────────────────────────────────────
        if self._check_and_handle_result():
            return

        # ── Back to human ─────────────────────────────────────────────────────
        self.human_turn = True
        self._set_status("Your turn  ( X )", C["status_turn"])

    # ─────────────────────────────────────────────────────────────────────────
    # Result checking
    # ─────────────────────────────────────────────────────────────────────────

    def _check_and_handle_result(self) -> bool:
        """Check for win/draw; return True if game is over."""
        winner = check_winner(self.board)

        if winner:
            win_line = get_winning_line(self.board)
            self._win_cells = list(win_line) if win_line else []

            if winner == HUMAN:
                msg = "You Win!  🎉"
                color = C["status_win"]
                self.scores["X"] += 1
            else:
                msg = "AI Wins!  🤖"
                color = C["status_win"]
                self.scores["O"] += 1

            self.game_active = False
            self._update_scoreboard()
            self._set_status(msg, color)
            self._start_win_glow()
            # Show overlay AFTER a short pause so the last symbol draws first
            self.after(350, lambda: self._show_game_over_overlay(msg, color))
            return True

        if is_draw(self.board):
            msg = "It's a Draw!  🤝"
            color = C["status_draw"]
            self.scores["Draw"] += 1
            self.game_active = False
            self._update_scoreboard()
            self._set_status(msg, color)
            self.after(350, lambda: self._show_game_over_overlay(msg, color))
            return True

        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Game-over overlay
    # ─────────────────────────────────────────────────────────────────────────

    def _show_game_over_overlay(self, message: str, color: str):
        """
        Place a semi-transparent overlay Frame over the canvas.
        Contains the result message and a prominent Play Again button.
        Removed automatically when _restart() is called.
        """
        # Remove any existing overlay first
        self._remove_overlay()

        TOTAL = CELL_SIZE * 3 + LINE_W * 2

        # Outer container (sits on top of the canvas via place)
        overlay = tk.Frame(self.canvas, bg="#07091a",
                           highlightthickness=2,
                           highlightbackground=color)
        overlay.place(x=TOTAL // 2, y=TOTAL // 2,
                      anchor="center",
                      width=TOTAL - 40, height=220)
        self._overlay_frame = overlay

        # Result emoji / icon row
        emoji = "🎉" if "Win" in message else ("🤖" if "AI" in message else "🤝")
        tk.Label(overlay, text=emoji,
                 font=("Segoe UI Emoji", 36),
                 bg="#07091a", fg=color).pack(pady=(22, 4))

        # Result text
        tk.Label(overlay, text=message,
                 font=self.fnt_status,
                 bg="#07091a", fg=color).pack()

        # Divider
        tk.Frame(overlay, height=1, bg=color).pack(fill="x",
                                                    padx=30, pady=12)

        # Play Again button (large, prominent)
        play_btn = tk.Label(
            overlay,
            text="  ↺   Play Again  ",
            font=self.fnt_btn,
            bg=color, fg="#07091a",
            padx=16, pady=10,
            cursor="hand2",
            relief="flat"
        )
        play_btn.pack()
        play_btn.bind("<Button-1>", lambda e: self._restart())
        play_btn.bind("<Enter>",
                      lambda e: play_btn.config(bg="#ffffff"))
        play_btn.bind("<Leave>",
                      lambda e: play_btn.config(bg=color))

    def _remove_overlay(self):
        """Destroy the game-over overlay if it exists."""
        if self._overlay_frame is not None:
            try:
                self._overlay_frame.destroy()
            except Exception:
                pass
            self._overlay_frame = None

    # ─────────────────────────────────────────────────────────────────────────
    # Win glow animation
    # ─────────────────────────────────────────────────────────────────────────

    def _start_win_glow(self):
        """Pulse the winning cells between gold and the cell idle colour."""
        self._glow_active = True
        self._glow_on     = True
        self._glow_pulse()

    def _glow_pulse(self):
        # Guard: stop silently if glow was cancelled
        if not self._glow_active or not self._win_cells:
            return
        color = C["win_glow"] if self._glow_on else C["cell_idle"]
        for idx in self._win_cells:
            self.canvas.itemconfig(self.cell_rects[idx], fill=color)
        self._glow_on = not self._glow_on
        self._glow_job = self.after(WIN_GLOW_MS * 5, self._glow_pulse)

    def _stop_win_glow(self):
        # Disable the guard FIRST so any in-flight callback exits immediately
        self._glow_active = False
        if self._glow_job:
            self.after_cancel(self._glow_job)
            self._glow_job = None
        for idx in range(9):
            self.canvas.itemconfig(self.cell_rects[idx], fill=C["cell_idle"])
        self._win_cells = []

    # ─────────────────────────────────────────────────────────────────────────
    # Controls: Restart, Toggle First Player
    # ─────────────────────────────────────────────────────────────────────────

    def _restart(self):
        """
        Reset the board and start a new game.

        Key fix: uses self._first_human (the stored preference) to decide
        who moves first — NOT self.human_turn which changes during play.
        This guarantees restart always works even mid-animation.
        """
        # 1. Remove the game-over overlay immediately
        self._remove_overlay()

        # 2. Stop win-glow animation
        self._stop_win_glow()

        # 3. If AI is still computing in the background, wait and retry.
        #    Force ai_thinking = False after game ends so this never loops.
        if self.ai_thinking:
            self.after(150, self._restart)
            return

        # 4. Clear board state
        self.board       = new_board()
        self.game_active = True
        self.ai_thinking = False

        # 5. Clear canvas symbols
        for idx in range(9):
            self._clear_cell_items(idx)
            self.canvas.itemconfig(self.cell_rects[idx], fill=C["cell_idle"])

        # 6. Reset stats labels
        self._nodes_ab.set("—")
        self._nodes_plain.set("—")
        self._ai_score.set("—")
        self._best_move.set("—")
        self._savings_var.set("")

        # 7. Decide who goes first using the PREFERENCE flag, not current turn
        self.human_turn = self._first_human
        if self._first_human:
            self._set_status("Your turn  ( X )", C["status_turn"])
        else:
            self._set_status("AI is thinking…", C["o_color"])
            self.ai_thinking = True
            threading.Thread(target=self._ai_move_thread, daemon=True).start()

    def _toggle_first(self):
        """Switch who plays first for future games."""
        self._first_human = not self._first_human
        label = "Human (X) plays first" if self._first_human else "AI (O) plays first"
        self._first_var.set(label)
        self._restart()

    # ─────────────────────────────────────────────────────────────────────────
    # UI helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str = None):
        self._status_var.set(text)
        # Directly recolor the stored label reference (fast, no tree search)
        try:
            self._status_lbl.config(fg=color or C["text_head"])
        except Exception:
            pass

    def _update_scoreboard(self):
        self._score_var.set(
            f"X: {self.scores['X']}     "
            f"O: {self.scores['O']}     "
            f"Draw: {self.scores['Draw']}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TicTacToeApp()
    app.mainloop()
