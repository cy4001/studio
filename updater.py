import sys
import os
import time
import requests
import subprocess
import ctypes
import time

def wait_for_process_termination(pid: int, timeout: int = 15) -> bool:
    """
    Waits for a Windows process to terminate using native OS synchronization.
    Avoids WinError 6 and CPU polling.
    """
    SYNCHRONIZE = 0x00100000
    WAIT_OBJECT_0 = 0x00000000
    WAIT_TIMEOUT = 0x00000102

    kernel32 = ctypes.windll.kernel32

    # Attempt to open process with synchronization rights
    process_handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    
    # If handle is 0/NULL, the process has already terminated
    if not process_handle:
        return True

    try:
        timeout_ms = int(timeout * 1000)
        # Blocks until the process closes or timeout expires
        result = kernel32.WaitForSingleObject(process_handle, timeout_ms)
        return result == WAIT_OBJECT_0
    finally:
        kernel32.CloseHandle(process_handle)
        
def main():
    if len(sys.argv) < 4:
        sys.exit(1)

    caller_pid = int(sys.argv[1])
    target_app_path = sys.argv[2]
    download_url = sys.argv[3]

    # 1. Wait for calling app to terminate
    wait_for_process_termination(caller_pid)

    # 2. Download new app.exe to a temp file
    temp_target_path = target_app_path + ".new"
    try:
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(temp_target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                f.write(chunk)
    except Exception as e:
        sys.exit(1)

    # 3. Replace target binary (up to 5 retries in case of filesystem lag)
    replaced = False
    for _ in range(5):
        try:
            if os.path.exists(target_app_path):
                os.remove(target_app_path)
            os.rename(temp_target_path, target_app_path)
            replaced = True
            break
        except PermissionError:
            time.sleep(1)

    # 4. Relaunch updated application
    if replaced and os.path.exists(target_app_path):
        subprocess.Popen([target_app_path])

if __name__ == "__main__":
    main()