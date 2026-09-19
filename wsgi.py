"""WSGI entry point for hosting WEMS (PythonAnywhere, or any WSGI server).

PythonAnywhere setup (Web tab -> WSGI configuration file):

    import sys
    path = '/home/YOURUSERNAME/wemsapp'   # your clone location
    if path not in sys.path:
        sys.path.insert(0, path)

    # Free accounts have no env-var panel, so set secrets here instead:
    # import os
    # os.environ['SECRET_KEY'] = 'paste-a-long-random-string-here'

    from wsgi import application

Local check:  python -c "from wsgi import application; print('ok')"
"""

import os
import sys
from dotenv import load_dotenv

# Make sure the app package is importable no matter where this file is loaded from.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_APP_DIR, '.env'))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from app import app as application  # noqa: E402

if __name__ == "__main__":
    application.run()
