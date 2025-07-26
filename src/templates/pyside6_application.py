from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont
from typing import Optional
import multiprocessing
import queue
from pathlib import Path

from config.settings import get_config


class PySide6Application(QMainWindow):
    """
    PySide6 main application window.
    
    Much simpler than the CustomTkinter version because Qt provides:
    - Built-in DPI awareness
    - Better window management
    - Automatic dark/light theme support
    - No need for custom window centering or sizing hacks
    """
    
    def __init__(self, parent: Optional[QMainWindow] = None):
        super().__init__(parent)
        self.config = get_config()
        self._setup_window()

    def _setup_window(self):
        """Set up the main window properties."""
        # Set window title
        self.setWindowTitle("BeanieDeploy")

        # Set a slightly larger default font
        font = QFont()
        font.setPointSize(12)  # Change 12 to your preferred size
        self.setFont(font)
        
        # Set window size and constraints
        self.resize(850, 580)
        self.setMinimumSize(800, 530)
        self.setMaximumSize(1450, 780)
        
        # Set window icon if available
        icon_path = self.config.paths.app_icon_path
        if icon_path and Path(icon_path).exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Set window flags for better behavior
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        
        # Center the window on screen
        self._center_window()

    def _center_window(self):
        """Center the window on the screen."""
        # Qt makes this much easier than CustomTkinter
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.geometry()
            
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            
            self.move(x, y)

    def wait_and_handle_queue_output(
        self,
        output_queue: multiprocessing.Queue,
        callback,
        frequency=100,
        retry_count=0,
    ):
        """
        Handle multiprocessing queue output.
        
        This is a simplified version of the CustomTkinter implementation.
        Qt's event loop handles this more efficiently.
        """
        try:
            while not output_queue.empty():
                output = output_queue.get_nowait()
                callback(output)
        except queue.Empty:
            if retry_count:
                # Use Qt's timer instead of tkinter's after method
                from PySide6.QtCore import QTimer
                QTimer.singleShot(
                    frequency,
                    lambda: self.wait_and_handle_queue_output(
                        output_queue, callback, frequency, retry_count - 1
                    )
                )
