import sys
from PyQt6.QtWidgets import QApplication
from MacropadGUI import MacropadGUI

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Macropad Configuration Tool")
    app.setApplicationVersion("1.0")
    
    # Create and show the main window
    window = MacropadGUI()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()