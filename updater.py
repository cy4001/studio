import sys
import os
import time
import requests
import subprocess

def wait_for_process_termination(pid: int, timeout: int = 15):
    """Wait until app.exe has completely exited to release file locks."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # os.kill with signal 0 checks process existence without killing
            os.kill(pid, 0)
            time.sleep(0.5)
        except OSError:
            return True
    return False

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