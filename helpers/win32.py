
WIN32_AVAILABLE = False

try:
    import win32api
    WIN32_AVAILABLE = True

except ImportError:
    pass


def getIdleTime():
    if WIN32_AVAILABLE:
        result = (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0
        print("DEBUG: Idle timer: %s" % str(result))
        return result
    else:
        print("Warning: getIdleTime not supported on non-win32 platforms.")
        return 0
