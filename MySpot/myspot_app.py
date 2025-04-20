import sys
from myspot.ui.gui import main as gui_main
from myspot.ui.cli import main as cli_main

if __name__ == "__main__":
    # Default to GUI mode
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--cli":
        cli_main()
    else:
        gui_main()
