import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.gui.app_window import ParkingApp
app = ParkingApp()
app.mainloop()
