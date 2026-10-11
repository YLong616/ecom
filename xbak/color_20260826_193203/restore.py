# -*- coding: utf-8 -*-
import shutil, os
base = os.path.dirname(os.path.abspath(__file__))
dst = os.path.join(base, "..", "..", "..", "ecom")
for n in ['app.py', 'at_panel.py', 'stress_panel.py', 'file_panel.py', 'tooltip.py']:
    src = os.path.join(base, n)
    shutil.copy2(src, os.path.join(dst, n))
print("RESTORED to", dst)
