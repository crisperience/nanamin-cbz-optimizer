import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QSlider,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QToolButton,
    QStyle,
    QSizePolicy,
    QDialog,
    QTabWidget,
    QTextBrowser,
    QScrollArea,
    QMenuBar,
    QMenu,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import (
    QIcon,
    QFont,
    QPalette,
    QColor,
    QKeySequence,
    QShortcut,
    QPainter,
    QPainterPath,
)
from utils.compressor import CBZCompressor
import zipfile
import shutil
import time
from pathlib import Path


class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(25)
        self.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #4C566A;
                border-radius: 5px;
                text-align: center;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 3px;
            }
        """
        )


class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
            QPushButton:disabled {
                background-color: #3B4252;
                color: #4C566A;
            }
        """
        )
        self.setMinimumHeight(35)


class ModernGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4C566A;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ECEFF4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #88C0D0;
            }
        """
        )


class ModernInfoIcon(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setStyleSheet(
            """
            QToolButton {
                border: none;
                padding: 4px;
                background: transparent;
                color: #88C0D0;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #4C566A;
                border-radius: 4px;
            }
        """
        )
        self.setToolTip("Click for help and keyboard shortcuts")
        self.setText("?")

    def paintEvent(self, event):
        # No custom painting needed, just use the text
        super().paintEvent(event)


class CompressionWorker(QThread):
    progress = pyqtSignal(
        int, int, int, str, float
    )  # total, processed, current_file, speed
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    aborted = pyqtSignal()

    def __init__(self, input_files, output_dir, quality):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.quality = quality
        self.compressor = CBZCompressor(quality)
        self._is_aborted = False

    def abort(self):
        self._is_aborted = True

    def run(self):
        try:
            results = {
                "total_files": len(self.input_files),
                "total_original_size": 0,
                "total_compressed_size": 0,
                "savings": 0,
                "processed_files": 0,
            }

            total_images = 0
            # First pass: count total images
            for input_file in self.input_files:
                temp_dir = Path(self.output_dir) / "temp_processing"
                temp_dir.mkdir(exist_ok=True)
                try:
                    with zipfile.ZipFile(input_file, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)
                        for root, _, files in os.walk(temp_dir):
                            for file in files:
                                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                                    total_images += 1
                finally:
                    shutil.rmtree(temp_dir)

            processed_images = 0
            start_time = time.time()

            for i, input_file in enumerate(self.input_files):
                if self._is_aborted:
                    self.aborted.emit()
                    return

                # Calculate original size
                original_size = self.compressor.get_file_size(input_file)
                results["total_original_size"] += original_size

                # Create output path
                output_file = os.path.join(
                    self.output_dir, os.path.basename(input_file)
                )

                # Compress file and get progress updates
                for (
                    file_total_images,
                    file_processed_images,
                    current_file,
                    speed,
                ) in self.compressor.compress_file(input_file, output_file):
                    if self._is_aborted:
                        self.aborted.emit()
                        return

                    processed_images += 1
                    total_progress = int((processed_images / total_images) * 100)
                    self.progress.emit(
                        total_images, processed_images, i + 1, current_file, speed
                    )

                # Calculate compressed size
                compressed_size = self.compressor.get_file_size(output_file)
                results["total_compressed_size"] += compressed_size
                results["processed_files"] += 1

            # Calculate total savings
            results["savings"] = self.compressor.calculate_savings(
                results["total_original_size"], results["total_compressed_size"]
            )

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help - Manga & Comic Optimizer")
        self.setMinimumSize(600, 400)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2E3440;
            }
            QTabWidget::pane {
                border: 1px solid #4C566A;
                background-color: #2E3440;
            }
            QTabBar::tab {
                background-color: #3B4252;
                color: #ECEFF4;
                padding: 8px 16px;
                border: 1px solid #4C566A;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #5E81AC;
            }
            QTextBrowser {
                background-color: #2E3440;
                color: #ECEFF4;
                border: none;
                padding: 10px;
            }
        """
        )

        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Getting Started tab
        getting_started = QTextBrowser()
        getting_started.setOpenExternalLinks(True)
        getting_started.setHtml(
            """
            <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                <div style="text-align: left;">
                    Click "Select CBZ Files" to choose your manga/comic files<br><br>
                    Select an output directory for the compressed files<br><br>
                    Adjust the quality setting if needed (85 is recommended)<br><br>
                    Click "Compress" to start the process
                </div>
            </div>
            """
        )

        # Quality Settings tab
        quality_settings = QTextBrowser()
        quality_settings.setOpenExternalLinks(True)
        quality_settings.setHtml(
            """
            <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                <div style="text-align: left;">
                    <b>100</b>: Maximum quality, largest file size<br><br>
                    <b>85</b>: Good balance (recommended)<br><br>
                    <b>70</b>: Smaller file size, slight quality loss<br><br>
                    <b>50</b>: Significant compression, noticeable quality loss
                </div>
            </div>
            """
        )

        # About tab
        about = QTextBrowser()
        about.setOpenExternalLinks(True)
        about.setHtml(
            """
            <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                <div style="text-align: left; margin-bottom: 20px;">
                    <span style="font-size: 24px; color: #88C0D0;">Nanamin 1.0.0</span>
                </div>
                
                <div style="text-align: left; margin-bottom: 20px;">
                    <a href="https://github.com/crisperience" style="color: #88C0D0; text-decoration: none; font-size: 16px;">📦 GitHub</a>
                </div>
                
                <div style="text-align: left;">
                    <a href="mailto:martin@crisp.hr" style="color: #88C0D0; text-decoration: none; font-size: 16px;">✉️ martin@crisp.hr</a>
                </div>
            </div>
            """
        )

        # Add tabs
        self.tab_widget.addTab(getting_started, "Getting Started")
        self.tab_widget.addTab(quality_settings, "Quality Settings")
        self.tab_widget.addTab(about, "About")

        layout.addWidget(self.tab_widget)

        # Add close button
        close_button = ModernButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manga & Comic Optimizer")
        self.setMinimumSize(900, 700)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 40, 20, 20)

        # Add help button to top-right corner
        help_button = ModernInfoIcon()
        help_button.clicked.connect(lambda: self.show_help_section(0))
        help_button.setParent(self)
        help_button.move(self.width() - 40, 15)

        # File selection group
        file_group = ModernGroupBox("Files")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(10)

        # Input files
        input_layout = QHBoxLayout()
        self.input_label = QLabel("No files selected")
        self.input_label.setStyleSheet("padding-left: 8px;")
        input_button = ModernButton("Select CBZ Files")
        input_button.clicked.connect(self.select_input_files)
        input_button.setToolTip("Select one or more CBZ files to compress")
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(input_button)
        file_layout.addLayout(input_layout)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_label = QLabel("No output directory selected")
        self.output_label.setStyleSheet("padding-left: 8px;")
        output_button = ModernButton("Select Output Directory")
        output_button.clicked.connect(self.select_output_directory)
        output_button.setToolTip("Select where to save compressed files")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(output_button)
        file_layout.addLayout(output_layout)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Compression settings group
        settings_group = ModernGroupBox("Compression Settings")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)

        # Quality slider with info icon
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        quality_label.setStyleSheet("padding-left: 8px;")
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 1px solid #4C566A;
                height: 12px;
                background: #3B4252;
                margin: 2px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #88C0D0;
                border: 1px solid #4C566A;
                width: 18px;
                height: 18px;
                margin: -3px 0;
                border-radius: 9px;
            }
        """
        )
        self.quality_value = QSpinBox()
        self.quality_value.setRange(1, 100)
        self.quality_value.setValue(85)
        self.quality_value.setButtonSymbols(
            QSpinBox.ButtonSymbols.NoButtons
        )  # Remove up/down arrows
        self.quality_slider.valueChanged.connect(self.quality_value.setValue)
        self.quality_value.valueChanged.connect(self.quality_slider.setValue)

        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        settings_layout.addLayout(quality_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Progress information
        progress_group = ModernGroupBox("Progress")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)  # Reverted back to original spacing

        # Progress bar
        self.progress_bar = ModernProgressBar()
        progress_layout.addWidget(self.progress_bar)

        # Detailed progress labels
        self.file_progress_label = QLabel("File: 0/0")
        self.file_progress_label.setStyleSheet(
            "padding-left: 8px;"
        )  # Removed top padding
        self.image_progress_label = QLabel("Images: 0/0")
        self.image_progress_label.setStyleSheet(
            "padding-left: 8px;"
        )  # Removed top padding
        self.current_file_label = QLabel("Current: -")
        self.current_file_label.setStyleSheet(
            "padding-left: 8px;"
        )  # Removed top padding
        self.speed_label = QLabel("Speed: 0.0 images/sec")
        self.speed_label.setStyleSheet("padding-left: 8px;")  # Removed top padding
        self.eta_label = QLabel("ETA: -")
        self.eta_label.setStyleSheet("padding-left: 8px;")  # Removed top padding

        progress_layout.addWidget(self.file_progress_label)
        progress_layout.addWidget(self.image_progress_label)
        progress_layout.addWidget(self.current_file_label)
        progress_layout.addWidget(self.speed_label)
        progress_layout.addWidget(self.eta_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Abort button
        self.abort_button = ModernButton("Abort")
        self.abort_button.clicked.connect(self.abort_compression)
        self.abort_button.setEnabled(False)
        self.abort_button.setToolTip("Abort current compression")
        button_layout.addWidget(self.abort_button)

        # Compress button
        self.compress_button = ModernButton("Compress")
        self.compress_button.clicked.connect(self.start_compression)
        self.compress_button.setToolTip("Start compression process")
        button_layout.addWidget(self.compress_button)

        # New Batch button
        self.new_batch_button = ModernButton("New Batch")
        self.new_batch_button.clicked.connect(self.reset_for_new_batch)
        self.new_batch_button.setToolTip("Start a new batch of files")
        self.new_batch_button.setEnabled(False)
        button_layout.addWidget(self.new_batch_button)

        layout.addLayout(button_layout)

        # Initialize variables
        self.input_files = []
        self.output_dir = ""
        self.worker = None
        self.start_time = None

        # Set up keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # File operations
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(
            self.select_input_files
        )
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(
            self.select_output_directory
        )
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(
            self.start_compression
        )
        QShortcut(QKeySequence("Ctrl+."), self).activated.connect(
            self.abort_compression
        )
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(
            self.reset_for_new_batch
        )

    def show_help_section(self, tab_index):
        """Show the help dialog with a specific tab selected."""
        dialog = HelpDialog(self)
        dialog.tab_widget.setCurrentIndex(tab_index)
        dialog.exec()

    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Manga & Comic Optimizer",
            """<h3>Manga & Comic Optimizer</h3>
            <p>A modern tool for optimizing manga and comic book files.</p>
            <p>Features:</p>
            <ul>
                <li>Efficient CBZ compression</li>
                <li>Quality-focused optimization</li>
                <li>Batch processing support</li>
                <li>Modern, user-friendly interface</li>
            </ul>
            <p>Version 1.0</p>""",
        )

    def select_input_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select CBZ Files", "", "CBZ Files (*.cbz);;All Files (*)"
        )
        if files:
            self.input_files = files
            self.input_label.setText(f"{len(files)} file(s) selected")

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", ""
        )
        if directory:
            self.output_dir = directory
            self.output_label.setText(directory)

    def start_compression(self):
        if not self.input_files:
            self.status_label.setText("Please select input files")
            return
        if not self.output_dir:
            self.status_label.setText("Please select output directory")
            return

        # Disable compression settings
        self.quality_slider.setEnabled(False)
        self.quality_value.setEnabled(False)

        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(True)
        self.status_label.setText("Compressing...")
        self.progress_bar.setValue(0)
        self.file_progress_label.setText("File: 0/0")
        self.image_progress_label.setText("Images: 0/0")
        self.current_file_label.setText("Current: -")
        self.speed_label.setText("Speed: 0.0 images/sec")
        self.eta_label.setText("ETA: -")

        self.start_time = time.time()
        self.worker = CompressionWorker(
            self.input_files, self.output_dir, self.quality_value.value()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.compression_finished)
        self.worker.error.connect(self.compression_error)
        self.worker.aborted.connect(self.compression_aborted)
        self.worker.start()

    def abort_compression(self):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.status_label.setText("Aborting...")
            self.abort_button.setEnabled(False)

    def update_progress(
        self, total_images, processed_images, current_file_num, current_file, speed
    ):
        total_files = len(self.input_files)
        self.progress_bar.setValue(int((processed_images / total_images) * 100))
        self.file_progress_label.setText(f"File: {current_file_num}/{total_files}")
        self.image_progress_label.setText(f"Images: {processed_images}/{total_images}")
        self.current_file_label.setText(f"Current: {current_file}")
        self.speed_label.setText(f"Speed: {speed:.1f} images/sec")

        # Calculate and display ETA
        if speed > 0:
            remaining_images = total_images - processed_images
            eta_seconds = remaining_images / speed
            if eta_seconds < 60:
                eta_text = f"{eta_seconds:.0f} seconds"
            elif eta_seconds < 3600:
                eta_text = f"{eta_seconds/60:.1f} minutes"
            else:
                eta_text = f"{eta_seconds/3600:.1f} hours"
            self.eta_label.setText(f"ETA: {eta_text}")

    def reset_for_new_batch(self):
        """Reset the UI for a new batch of files"""
        self.input_files = []
        self.input_label.setText("No files selected")
        self.output_label.setText("No output directory selected")
        self.output_dir = ""
        self.progress_bar.setValue(0)
        self.file_progress_label.setText("File: 0/0")
        self.image_progress_label.setText("Images: 0/0")
        self.current_file_label.setText("Current: -")
        self.speed_label.setText("Speed: 0.0 images/sec")
        self.eta_label.setText("ETA: -")
        self.status_label.setText("")
        self.compress_button.setEnabled(True)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(False)

    def compression_finished(self, results):
        # Re-enable compression settings
        self.quality_slider.setEnabled(True)
        self.quality_value.setEnabled(True)

        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(True)
        self.status_label.setText("Compression completed")
        self.progress_bar.setValue(100)

        # Show compression results
        message = (
            f"Compression completed!\n\n"
            f"Files processed: {results['processed_files']}/{results['total_files']}\n"
            f"Original size: {results['total_original_size']:.2f} MB\n"
            f"Compressed size: {results['total_compressed_size']:.2f} MB\n"
            f"Space saved: {results['savings']:.1f}%"
        )
        QMessageBox.information(self, "Compression Results", message)

    def compression_error(self, error):
        # Re-enable compression settings
        self.quality_slider.setEnabled(True)
        self.quality_value.setEnabled(True)

        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(True)
        self.status_label.setText(f"Error: {error}")
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error}")

    def compression_aborted(self):
        # Re-enable compression settings
        self.quality_slider.setEnabled(True)
        self.quality_value.setEnabled(True)

        self.compress_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.new_batch_button.setEnabled(True)
        self.status_label.setText("Compression aborted")
        QMessageBox.information(self, "Aborted", "Compression was aborted by user.")

    def resizeEvent(self, event):
        """Handle window resize to keep help button in top-right corner."""
        super().resizeEvent(event)
        # Find the help button and update its position with padding
        for child in self.findChildren(ModernInfoIcon):
            child.move(self.width() - 40, 15)


def main():
    # Initialize necessary directories
    home = str(Path.home())
    app_data = os.path.join(home, ".nanamin")
    os.makedirs(app_data, exist_ok=True)
    os.chmod(app_data, 0o755)

    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Set application palette for Nord theme
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(46, 52, 64))  # nord0
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.Base, QColor(59, 66, 82))  # nord1
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(46, 52, 64))  # nord0
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(46, 52, 64))  # nord0
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.Button, QColor(59, 66, 82))  # nord1
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 239, 244))  # nord6
    palette.setColor(QPalette.ColorRole.BrightText, QColor(191, 97, 106))  # nord11
    palette.setColor(QPalette.ColorRole.Link, QColor(94, 129, 172))  # nord10
    palette.setColor(QPalette.ColorRole.Highlight, QColor(94, 129, 172))  # nord10
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(236, 239, 244))  # nord6
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
