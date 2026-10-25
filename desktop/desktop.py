import tkinter as tk
from tkinter import ttk
from collections import deque

from hanoi import solve_from_state


BACKGROUND = "#101715"
PANEL = "#1a2420"
TEXT = "#f1f4e8"
MUTED = "#a4b3a8"
ACCENT = "#d2ed80"

COLORS = [
    "#f5cd78",
    "#e8a684",
    "#a9d7bf",
    "#83c3d0",
    "#b4a6dc",
    "#d0b6d0",
    "#c0d989",
    "#86b9ac",
]


class HanoiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tower of Hanoi — Python")
        self.root.geometry("940x740")
        self.root.minsize(700, 640)
        self.root.configure(bg=BACKGROUND)

        self.disk_count = tk.IntVar(value=5)
        self.speed = tk.IntVar(value=3)
        self.status = tk.StringVar()
        self.counter = tk.StringVar()

        self.pegs = []
        self.history = []
        self.solution = deque()
        self.selected = None

        self.playing = False
        self.timer = None

        self.build_interface()
        self.reset()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_interface(self):
        main = tk.Frame(self.root, bg=BACKGROUND)
        main.pack(fill="both", expand=True, padx=26, pady=22)

        tk.Label(
            main,
            text="THE RECURSION PLAYGROUND",
            bg=BACKGROUND,
            fg=ACCENT,
            font=("Helvetica", 11, "bold"),
        ).pack(anchor="w")

        tk.Label(
            main,
            text="Tower of Hanoi",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Helvetica", 32, "bold"),
        ).pack(anchor="w", pady=(8, 6))

        tk.Label(
            main,
            text=(
                "Move every disk from A to C. "
                "Never place a larger disk on a smaller one."
            ),
            bg=BACKGROUND,
            fg=MUTED,
            font=("Helvetica", 12),
            wraplength=800,
            justify="left",
        ).pack(anchor="w")

        settings = tk.Frame(main, bg=BACKGROUND)
        settings.pack(fill="x", pady=18)

        tk.Label(
            settings,
            text="Disks",
            bg=BACKGROUND,
            fg=TEXT,
        ).pack(side="left", padx=(0, 8))

        count_picker = ttk.Combobox(
            settings,
            textvariable=self.disk_count,
            values=(3, 4, 5, 6, 7, 8),
            width=4,
            state="readonly",
        )
        count_picker.pack(side="left")
        count_picker.bind(
            "<<ComboboxSelected>>",
            lambda event: self.reset(),
        )

        tk.Label(
            settings,
            text="Speed",
            bg=BACKGROUND,
            fg=TEXT,
        ).pack(side="left", padx=(25, 8))

        ttk.Scale(
            settings,
            from_=1,
            to=5,
            variable=self.speed,
            length=150,
        ).pack(side="left")

        tk.Label(
            main,
            textvariable=self.counter,
            bg=BACKGROUND,
            fg=ACCENT,
            font=("Helvetica", 14, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.canvas = tk.Canvas(
            main,
            bg=PANEL,
            height=300,
            highlightthickness=1,
            highlightbackground="#394d3e",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.canvas.bind("<Button-1>", self.on_board_click)

        tk.Label(
            main,
            textvariable=self.status,
            bg=BACKGROUND,
            fg=MUTED,
            font=("Helvetica", 12),
            wraplength=800,
            justify="center",
        ).pack(fill="x", pady=14)

        controls = tk.Frame(main, bg=BACKGROUND)
        controls.pack()

        self.play_button = ttk.Button(
            controls,
            text="Play solution",
            command=self.toggle_play,
        )
        self.play_button.pack(side="left", padx=5)

        self.step_button = ttk.Button(
            controls,
            text="Next move",
            command=self.step,
        )
        self.step_button.pack(side="left", padx=5)

        self.undo_button = ttk.Button(
            controls,
            text="Undo",
            command=self.undo,
        )
        self.undo_button.pack(side="left", padx=5)

        ttk.Button(
            controls,
            text="Reset",
            command=self.reset,
        ).pack(side="left", padx=5)

        tk.Label(
            main,
            text=(
                "RECURSION: move n − 1 disks aside → "
                "move the largest disk → move n − 1 disks onto it\n"
                "Minimum moves: 2ⁿ − 1   |   "
                "Time: O(2ⁿ)   |   Recursive stack: O(n)"
            ),
            bg=BACKGROUND,
            fg=MUTED,
            font=("Helvetica", 11),
            wraplength=800,
            justify="center",
        ).pack(pady=(20, 0))

    def is_solved(self):
        return len(self.pegs[2]) == self.disk_count.get()

    def reset(self):
        self.pause()

        number = self.disk_count.get()
        self.pegs = [list(range(number, 0, -1)), [], []]
        self.history = []
        self.solution = deque()
        self.selected = None

        self.status.set("Click a tower, then click its destination.")
        self.refresh()

    def refresh(self):
        minimum = 2 ** self.disk_count.get() - 1

        self.counter.set(
            f"Moves: {len(self.history)}     Minimum: {minimum}"
        )

        self.play_button.configure(
            text="Pause" if self.playing else "Play solution",
            state="disabled" if self.is_solved() else "normal",
        )

        self.step_button.configure(
            state=(
                "disabled"
                if self.playing or self.is_solved()
                else "normal"
            )
        )

        self.undo_button.configure(
            state=(
                "normal"
                if self.history and not self.playing
                else "disabled"
            )
        )

        self.draw()

    def draw(self):
        if not self.pegs:
            return

        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 10 or height < 10:
            return

        section_width = width / 3
        base_y = height - 42
        disk_height = min(26, (height - 90) / 8)
        number = self.disk_count.get()

        for index, stack in enumerate(self.pegs):
            center_x = section_width * (index + 0.5)

            if self.selected == index:
                self.canvas.create_rectangle(
                    index * section_width + 8,
                    12,
                    (index + 1) * section_width - 8,
                    base_y + 12,
                    outline=ACCENT,
                    width=2,
                    dash=(5, 4),
                )

            self.canvas.create_line(
                center_x,
                40,
                center_x,
                base_y,
                fill="#9aaa91",
                width=7,
                capstyle=tk.ROUND,
            )

            self.canvas.create_line(
                center_x - section_width * 0.43,
                base_y + 4,
                center_x + section_width * 0.43,
                base_y + 4,
                fill="#667b62",
                width=9,
                capstyle=tk.ROUND,
            )

            for level, disk in enumerate(stack):
                disk_width = section_width * (
                    0.23 + 0.63 * disk / number
                )

                bottom = base_y - level * (disk_height + 3)
                top = bottom - disk_height

                if (
                    self.selected == index
                    and level == len(stack) - 1
                ):
                    top -= 12
                    bottom -= 12

                self.canvas.create_rectangle(
                    center_x - disk_width / 2,
                    top,
                    center_x + disk_width / 2,
                    bottom,
                    fill=COLORS[disk - 1],
                    outline="#e3ead7",
                    width=1,
                )

                self.canvas.create_text(
                    center_x,
                    (top + bottom) / 2,
                    text=str(disk),
                    fill="#172017",
                    font=("Helvetica", 11, "bold"),
                )

            self.canvas.create_text(
                center_x,
                height - 17,
                text="ABC"[index],
                fill=TEXT,
                font=("Helvetica", 13, "bold"),
            )

    def on_board_click(self, event):
        if self.playing or self.is_solved():
            return

        section_width = self.canvas.winfo_width() / 3
        index = min(2, max(0, int(event.x / section_width)))

        if self.selected is None:
            if not self.pegs[index]:
                self.status.set("That tower is empty.")
                return

            self.selected = index
            disk = self.pegs[index][-1]

            self.status.set(
                f"Disk {disk} selected. Click its destination."
            )

        elif self.selected == index:
            self.selected = None
            self.status.set("Selection cleared.")

        else:
            if not self.move_disk(self.selected, index):
                self.status.set(
                    "Invalid move: a larger disk cannot "
                    "sit on a smaller disk."
                )
                return

            self.selected = None
            self.solution.clear()

        self.refresh()

    def move_disk(self, source, destination):
        if not self.pegs[source]:
            return False

        disk = self.pegs[source][-1]

        if (
            self.pegs[destination]
            and self.pegs[destination][-1] < disk
        ):
            return False

        self.pegs[source].pop()
        self.pegs[destination].append(disk)
        self.history.append((source, destination))

        if self.is_solved():
            minimum = 2 ** self.disk_count.get() - 1

            result = (
                "Perfect solution!"
                if len(self.history) == minimum
                else f"The minimum is {minimum}."
            )

            self.status.set(
                f"Solved in {len(self.history)} moves! {result}"
            )
        else:
            self.status.set(
                f"Move {len(self.history)}: disk {disk}, "
                f"{'ABC'[source]} → {'ABC'[destination]}."
            )

        return True

    def step(self):
        if self.is_solved():
            return

        self.selected = None

        if not self.solution:
            self.solution = deque(
                solve_from_state(
                    self.pegs,
                    self.disk_count.get(),
                )
            )

        if self.solution:
            source, destination = self.solution.popleft()
            self.move_disk(source, destination)

        self.refresh()

    def toggle_play(self):
        if self.playing:
            self.pause()
            self.refresh()
            return

        if self.is_solved():
            return

        self.playing = True
        self.tick()

    def tick(self):
        self.timer = None

        if not self.playing:
            return

        self.step()

        if self.is_solved():
            self.pause()
            self.refresh()
            return

        delay = int(1500 - float(self.speed.get()) * 240)
        self.timer = self.root.after(max(100, delay), self.tick)

    def pause(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None

        self.playing = False

    def undo(self):
        self.pause()

        if not self.history:
            return

        source, destination = self.history.pop()
        self.pegs[source].append(self.pegs[destination].pop())

        self.selected = None
        self.solution.clear()

        self.status.set("Move undone.")
        self.refresh()

    def close(self):
        self.pause()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HanoiApp(root)
    root.mainloop()