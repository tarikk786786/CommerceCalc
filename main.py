"""
CommerceCalc — Application entry point.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.db.database import init_db, get_session_factory
from src.ui.main_window import MainWindow


def main():
    # Set explicit AppUserModelID so Windows taskbar shows the correct icon
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("commercecalc.desktop.suite.v1")
    except Exception:
        pass

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("CommerceCalc")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CommerceCalc")
    app.setOrganizationDomain("commercecalc.local")

    # Set Application Icon
    icon_path = Path(__file__).parent / "assets" / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Initialize database
    try:
        engine = init_db()
        SessionFactory = get_session_factory(engine)
        session = SessionFactory()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Database Error",
            f"Failed to initialize database:\n{str(e)}\n\n"
            "The application will run without data persistence."
        )
        session = None

    # Launch main window
    window = MainWindow(db_session=session)
    window.show()

    result = app.exec()

    # Cleanup
    if session:
        session.close()

    sys.exit(result)


if __name__ == "__main__":
    main()
