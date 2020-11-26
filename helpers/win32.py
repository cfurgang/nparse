
WIN32_AVAILABLE = False

try:
    import win32api
    WIN32_AVAILABLE = True

except ImportError:
    pass


def getIdleTime():
    if WIN32_AVAILABLE:
        result = (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0
        return result
    else:
        return 0
