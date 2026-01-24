import sys
import os
import time
import keyboard
import ctypes

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QSystemTrayIcon,
    QMenu,
    QAction
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon

import win32gui
import win32con


class TransparentWindow(QWidget):
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
            pix = QPixmap(os.path.join(frames_dir, f"frame_{i:03}.png"))
            if not pix.isNull():
                self.idle_frames.append(pix)

        self.hit_left = QPixmap(os.path.join(frames_dir, "hit_left.png"))
        self.hit_right = QPixmap(os.path.join(frames_dir, "hit_right.png"))
        self.hit_both = QPixmap(os.path.join(frames_dir, "hit_both.png"))

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

        # ---------------- Keyboard ----------------
        self.keyPressed.connect(self.handle_key_qt)
        keyboard.on_press(self.on_key_background)

        # ---------------- Dragging ----------------
        self.drag_pos = QPoint()

        # ---------------- Click-Through ----------------
        self.click_through = False

        # ---------------- Tray Icon ----------------
        self.init_tray()

    # --------------------------------------------------
    # Tray Icon
    # --------------------------------------------------
    def init_tray(self):
        self.tray = QSystemTrayIcon(self)

        icon_path = os.path.join(os.path.dirname(sys.argv[0]), "frames", "frame_000.png")
        self.tray.setIcon(QIcon(icon_path))
        self.tray.setToolTip("BongoCat Overlay")

        menu = QMenu()

        self.click_action = QAction("Click-Through: OFF", self)
        self.click_action.triggered.connect(self.toggle_click_through)
        menu.addAction(self.click_action)

        self.visibility_action = QAction("Hide Window", self)
        self.visibility_action.triggered.connect(self.toggle_visibility)
        menu.addAction(self.visibility_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    # --------------------------------------------------
    # Click-Through (Win32)
    # --------------------------------------------------
    def toggle_click_through(self):
        hwnd = int(self.winId())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

        if not self.click_through:
            win32gui.SetWindowLong(
                hwnd,
                win32con.GWL_EXSTYLE,
                style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            )
            self.click_through = True
            self.click_action.setText("Click-Through: ON")
        else:
            win32gui.SetWindowLong(
                hwnd,
                win32con.GWL_EXSTYLE,
                style & ~win32con.WS_EX_TRANSPARENT
            )
            self.click_through = False
            self.click_action.setText("Click-Through: OFF")

    # --------------------------------------------------
    # Visibility
    # --------------------------------------------------
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.visibility_action.setText("Show Window")
        else:
            self.show()
            self.visibility_action.setText("Hide Window")

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
        self.keyPressed.emit()

    # --------------------------------------------------
    # Keyboard (Qt Thread)
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

    # --------------------------------------------------
    # Quit
    # --------------------------------------------------
    def quit_app(self):
        keyboard.unhook_all()
        QApplication.quit()


# ------------------------------------------------------
# Main
# ------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec_())
