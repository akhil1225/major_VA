import subprocess


def shutdown() -> str:
    subprocess.Popen(["shutdown", "/s", "/t", "0"])
    return "Shutting down the system."


def restart() -> str:
    subprocess.Popen(["shutdown", "/r", "/t", "0"])
    return "Restarting the system."


def sleep() -> str:
    subprocess.Popen(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
        shell=False
    )
    return "Putting the system to sleep."


def lock() -> str:
    subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Locking the system."


def hibernate() -> str:
    subprocess.Popen(
        ["shutdown", "/h"],
        shell=False
    )
    return "Hibernating the system."
