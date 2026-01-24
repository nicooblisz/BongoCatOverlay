import sys
import os
import time
import keyboard

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap


class TransparentWindow(QWidget):
    # Thread-sicheres Signal für Tastendrücke
    keyPressed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ---------------- Window Setup ----------------
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 300)
        self.move(100, 100)

        # ---------------- Image View ----------------
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 300, 300)
        self.label.setScaledContents(True)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setStyleSheet("background: transparent;")

        # ---------------- Load Frames ----------------
        base_dir = os.path.dirname(sys.argv[0])
        frames_dir = os.path.join(base_dir, "frames")

        self.idle_frames = []
        for i in range(3):
            path = os.path.join(frames_dir, f"frame_{i:03}.png")
            pix = QPixmap(path)
            print(f"Loaded {path}: valid={not pix.isNull()}")
            if not pix.isNull():
                self.idle_frames.append(pix)

        self.hit_left = QPixmap(os.path.join(frames_dir, "hit_left.png"))
        self.hit_right = QPixmap(os.path.join(frames_dir, "hit_right.png"))
        self.hit_both = QPixmap(os.path.join(frames_dir, "hit_both.png"))

        print("hit_left valid:", not self.hit_left.isNull())
        print("hit_right valid:", not self.hit_right.isNull())
        print("hit_both valid:", not self.hit_both.isNull())

        # ---------------- Initial Frame ----------------
        self.frame_index = 0
        if self.idle_frames:
            self.label.setPixmap(self.idle_frames[0])

        # ---------------- Animation State ----------------
        self.is_left = True
        self.last_key_time = 0.0
        self.double_threshold = 0.05

        # ---------------- Idle Animation Timer ----------------
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

        # ---------------- Keyboard Handling ----------------
        self.keyPressed.connect(self.handle_key_qt)
        keyboard.on_press(self.on_key_background)

        # ---------------- Dragging ----------------
        self.drag_pos = QPoint()

    # --------------------------------------------------
    # Idle Animation
    # --------------------------------------------------
    def update_frame(self):
        if not self.idle_frames:
            return
        self.label.setPixmap(self.idle_frames[self.frame_index])
        self.frame_index = (self.frame_index + 1) % len(self.idle_frames)

    # --------------------------------------------------
    # Keyboard (Background Thread)
    # --------------------------------------------------
    def on_key_background(self, event):
        # KEIN Qt-Zugriff hier!
        self.keyPressed.emit()

    # --------------------------------------------------
    # Keyboard (Qt Main Thread)
    # --------------------------------------------------
    def handle_key_qt(self):
        now = time.time()

        if now - self.last_key_time < self.double_threshold:
            self.show_hit(self.hit_both)
            self.last_key_time = 0.0
        else:
            self.last_key_time = now
            self.show_hit(self.hit_left if self.is_left else self.hit_right)
            self.is_left = not self.is_left

    # --------------------------------------------------
    # Hit Animation
    # --------------------------------------------------
    def show_hit(self, pixmap):
        if pixmap.isNull():
            return
        self.timer.stop()
        self.label.setPixmap(pixmap)
        QTimer.singleShot(100, self.timer.start)

    # --------------------------------------------------
    # Drag-to-move
    # --------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)


# ------------------------------------------------------
# Main
# ------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec_())
