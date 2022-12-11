#!/usr/bin/env python
import sys

if "-g" in sys.argv:
    import d4m.gui.main

    d4m.gui.main.main()
else:
    import d4m.tui

    d4m.tui.main()
