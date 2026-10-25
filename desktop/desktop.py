import tkinter as tk
import time
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
        self.speed = tk.DoubleVar(value=3)
        self.status = tk.StringVar()
        self.counter = tk.StringVar()

        self.pegs = []
        self.history = []
        self.solution = deque()
        self.selected = None

        self.playing = False
        self.timer = None

        self.animation_timer = None
        self.animation = None

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

        self.cancel_animation()

        number = self.disk_count.get()
        self.pegs = [list(range(number, 0, -1)), [], []]
        self.history = []
        self.solution = deque()
        self.selected = None

        self.status.set("Click a tower, then click its destination.")
        self.refresh()

    def refresh(self):
        
        minimum = 2 ** self.disk_count.get() - 1
        busy = self.playing or self.animation is not None

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
                if busy or self.is_solved()
                else "normal"
            )
        )

        self.undo_button.configure(
            state=(
                "normal"
                if self.history and not busy
                else "disabled"
            )
        )

        self.draw()

    def board_geometry(self):
        width = max(10, self.canvas.winfo_width())
        height = max(10, self.canvas.winfo_height())

        section_width = width / 3
        base_y = height - 42
        disk_height = min(26, (height - 90) / 8)

        return width, height, section_width, base_y, disk_height

    def paint_disk(self, disk, center_x, center_y):
        _, _, section_width, _, disk_height = (
            self.board_geometry()
        )

        disk_width = section_width * (
            0.23 + 0.63 * disk / self.disk_count.get()
        )

        left = center_x - disk_width / 2
        right = center_x + disk_width / 2
        top = center_y - disk_height / 2
        bottom = center_y + disk_height / 2

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=COLORS[disk - 1],
            outline="#e3ead7",
            width=1,
        )

        # A thin highlight gives the disk some depth.
        self.canvas.create_line(
            left + 2,
            top + 3,
            right - 2,
            top + 3,
            fill="#ffffff",
            width=1,
        )

        self.canvas.create_text(
            center_x,
            center_y,
            text=str(disk),
            fill="#172017",
            font=("Helvetica", 11, "bold"),
        )

    def draw(self):
        if not self.pegs:
            return

        self.canvas.delete("all")

        (
            width,
            height,
            section_width,
            base_y,
            disk_height,
        ) = self.board_geometry()

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
                # The moving disk is drawn separately.
                if (
                    self.animation is not None
                    and index == self.animation["destination"]
                    and level == len(stack) - 1
                ):
                    continue

                center_y = (
                    base_y
                    - level * (disk_height + 3)
                    - disk_height / 2
                )

                if (
                    self.selected == index
                    and level == len(stack) - 1
                ):
                    center_y -= 12

                self.paint_disk(disk, center_x, center_y)

            self.canvas.create_text(
                center_x,
                height - 17,
                text="ABC"[index],
                fill=TEXT,
                font=("Helvetica", 13, "bold"),
            )

        if self.animation is not None:
            self.draw_moving_disk()

    @staticmethod
    def ease(value):
        """Smooth acceleration and deceleration."""
        return value * value * (3 - 2 * value)

    def draw_moving_disk(self):
        animation = self.animation

        _, _, section_width, base_y, disk_height = (
            self.board_geometry()
        )

        start_x = section_width * (
            animation["source"] + 0.5
        )
        end_x = section_width * (
            animation["destination"] + 0.5
        )

        start_y = (
            base_y
            - animation["source_level"] * (disk_height + 3)
            - disk_height / 2
            - animation["lift_offset"]
        )

        end_y = (
            base_y
            - animation["destination_level"]
            * (disk_height + 3)
            - disk_height / 2
        )

        # Above the tops of the rods.
        travel_y = 20

        progress = animation["progress"]

        if progress < 0.3:
            fraction = self.ease(progress / 0.3)

            x = start_x
            y = start_y + (travel_y - start_y) * fraction

        elif progress < 0.7:
            fraction = self.ease((progress - 0.3) / 0.4)

            x = start_x + (end_x - start_x) * fraction
            y = travel_y

        else:
            fraction = self.ease((progress - 0.7) / 0.3)

            x = end_x
            y = travel_y + (end_y - travel_y) * fraction

        self.paint_disk(animation["disk"], x, y)

    def animate_frame(self):
        self.animation_timer = None

        if self.animation is None:
            return

        elapsed = time.perf_counter() - self.animation["started"]
        duration = self.animation["duration"]

        self.animation["progress"] = min(1.0, elapsed / duration)

        if self.animation["progress"] >= 1.0:
            self.animation = None
            self.refresh()

            if self.playing:
                if self.is_solved():
                    self.pause()
                    self.refresh()
                else:
                    self.timer = self.root.after(120, self.tick)

            return

        self.draw()

        self.animation_timer = self.root.after(
            16,
            self.animate_frame,
        )

    def cancel_animation(self):
        if self.animation_timer is not None:
            self.root.after_cancel(self.animation_timer)
            self.animation_timer = None

        self.animation = None

    def on_board_click(self, event):
        if (
            self.playing
            or self.animation is not None
            or self.is_solved()
        ):
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
        if self.animation is not None:
            return False

        if source == destination or not self.pegs[source]:
            return False

        disk = self.pegs[source][-1]

        if (
            self.pegs[destination]
            and self.pegs[destination][-1] < disk
        ):
            return False

        source_level = len(self.pegs[source]) - 1
        destination_level = len(self.pegs[destination])

        lift_offset = 12 if self.selected == source else 0

        self.pegs[source].pop()
        self.pegs[destination].append(disk)
        self.history.append((source, destination))

        speed = float(self.speed.get())

        self.animation = {
            "disk": disk,
            "source": source,
            "destination": destination,
            "source_level": source_level,
            "destination_level": destination_level,
            "lift_offset": lift_offset,
            "started": time.perf_counter(),
            "duration": 1.5 - speed * 0.22,
            "progress": 0.0,
        }

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

        self.animate_frame()
        return True

    def step(self):
        if self.animation is not None or self.is_solved():
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

        # If a disk is already moving, its completion
        # callback will start the next automatic move.
        if self.animation is None:
            self.tick()
        else:
            self.refresh()

    def tick(self):
        self.timer = None

        if not self.playing or self.animation is not None:
            return

        if self.is_solved():
            self.pause()
            self.refresh()
            return

        self.step()

    def pause(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None

        self.playing = False

    def undo(self):
        if self.animation is not None:
            return
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
        self.cancel_animation()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HanoiApp(root)
    root.mainloop()