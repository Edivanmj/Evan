import math
import threading
import time
import tkinter as tk


class EvanFace:
    def __init__(self):
        self.mode = "idle"
        self.running = False
        self.stop_requested = False

        self._lock = threading.Lock()
        self._ready = threading.Event()

        self.root = None
        self.canvas = None

        self.left_eye = None
        self.right_eye = None
        self.left_pupil = None
        self.right_pupil = None
        self.mouth = None
        self.status_text = None

    def start(self):
        if self.running:
            return

        self.running = True
        self.stop_requested = False

        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

        self._ready.wait(timeout=3)

    def set_mode(self, mode: str):
        with self._lock:
            self.mode = mode

    def idle(self):
        self.set_mode("idle")

    def listening(self):
        self.set_mode("listening")

    def speaking(self):
        self.set_mode("speaking")

    def close(self):
        self.stop_requested = True

    def _run(self):
        self.root = tk.Tk()
        self.root.title("EVAN OS - Face")
        self.root.geometry("700x500")
        self.root.configure(bg="#050510")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=700,
            height=500,
            bg="#050510",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Cabeça / tela
        self.canvas.create_oval(
            110,
            60,
            590,
            440,
            outline="#00bfff",
            width=4,
            fill="#080820",
        )

        # Olhos
        self.left_eye = self.canvas.create_oval(
            190,
            160,
            290,
            230,
            outline="#00ffff",
            width=3,
            fill="#00d9ff",
        )

        self.right_eye = self.canvas.create_oval(
            410,
            160,
            510,
            230,
            outline="#00ffff",
            width=3,
            fill="#00d9ff",
        )

        self.left_pupil = self.canvas.create_oval(
            230,
            185,
            250,
            205,
            fill="#001020",
            outline="",
        )

        self.right_pupil = self.canvas.create_oval(
            450,
            185,
            470,
            205,
            fill="#001020",
            outline="",
        )

        # Boca
        self.mouth = self.canvas.create_oval(
            290,
            315,
            410,
            335,
            outline="#00ffff",
            width=3,
            fill="#001020",
        )

        # Nome
        self.canvas.create_text(
            350,
            35,
            text="EVAN OS",
            fill="#00ffff",
            font=("Arial", 24, "bold"),
        )

        self.status_text = self.canvas.create_text(
            350,
            465,
            text="AGUARDANDO",
            fill="#00ffff",
            font=("Arial", 16, "bold"),
        )

        self._ready.set()
        self._animate()

        self.root.mainloop()

    def _animate(self):
        if self.stop_requested:
            try:
                self.root.destroy()
            except Exception:
                pass
            return

        with self._lock:
            mode = self.mode

        now = time.time()

        # Piscar
        blink = now % 5 > 4.85

        if mode == "idle":
            eye_color = "#00d9ff"
            outline_color = "#00ffff"
            status = "AGUARDANDO"
            mouth_height = 10

        elif mode == "listening":
            eye_color = "#00ff88"
            outline_color = "#00ff88"
            status = "OUVINDO"
            mouth_height = 14

        elif mode == "speaking":
            eye_color = "#ffaa00"
            outline_color = "#ffaa00"
            status = "FALANDO"
            mouth_height = 18 + abs(math.sin(now * 12)) * 55

        else:
            eye_color = "#00d9ff"
            outline_color = "#00ffff"
            status = "AGUARDANDO"
            mouth_height = 10

        if blink:
            left_eye_coords = (190, 192, 290, 202)
            right_eye_coords = (410, 192, 510, 202)
        else:
            left_eye_coords = (190, 160, 290, 230)
            right_eye_coords = (410, 160, 510, 230)

        try:
            self.canvas.coords(self.left_eye, *left_eye_coords)
            self.canvas.coords(self.right_eye, *right_eye_coords)

            self.canvas.itemconfig(self.left_eye, fill=eye_color, outline=outline_color)
            self.canvas.itemconfig(self.right_eye, fill=eye_color, outline=outline_color)

            self.canvas.itemconfig(self.mouth, outline=outline_color)

            center_y = 325
            self.canvas.coords(
                self.mouth,
                290,
                center_y - mouth_height / 2,
                410,
                center_y + mouth_height / 2,
            )

            self.canvas.itemconfig(self.status_text, text=status, fill=outline_color)

        except Exception:
            return

        self.root.after(50, self._animate)