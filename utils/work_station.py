import getpass
import os
import re
import socket
import uuid


def _get_workstation_info():
    # Hostname and IP
    try:
        h, i = socket.gethostname(), socket.gethostbyname(socket.gethostname())
    except:
        h, i = 'Unknown', 'N/A'

    # MAC Address
    try:
        m = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    except:
        m = 'N/A'

    # Local User Account (with fallback)
    try:
        u = os.getlogin()
    except:
        u = getpass.getuser()

    # Combine as "HOSTNAME\Username"
    full_user = f"{h}\\{u}"

    return {"h": h, "i": i, "m": m, "u": full_user}