from config import appconf
import subprocess
import sys
import threading

sys.stdout.reconfigure(line_buffering=True)
def stream_output(stream, prefix):
    """
    Read the output of the child process in real time and print it to the console
    """
    for line in iter(stream.readline, b""):
        if not line.strip():
            continue
        sys.stdout.write(f"{prefix}{line}")
    stream.close()

def start_gunicorn(app_module, host=appconf['bind'], port=appconf['port'], workers=1):
    """
    Start the Gunicorn server
    """
    command = [
        "gunicorn",
        f"{app_module}:app",
        "--bind", f"{host}:{port}",
        "--workers", str(workers),
    ]
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True
    )

def start_py(script_path):
    """
    Start common py
    """
    command = ["python", script_path]
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True
    )

def main():
    flask_app_module = "webapp"
    bluebird_module = "bluebird.py"

    gunicorn_process = start_gunicorn(flask_app_module)
    bluebird_process = start_py(bluebird_module)

    threads = [
        threading.Thread(target=stream_output, args=(gunicorn_process.stdout, "[Gunicorn] ")),
        threading.Thread(target=stream_output, args=(gunicorn_process.stderr, "[Gunicorn-Error] ")),
        threading.Thread(target=stream_output, args=(bluebird_process.stdout, "[Bluebird] ")),
        threading.Thread(target=stream_output, args=(bluebird_process.stderr, "[Bluebird-Error] ")),
    ]

    for thread in threads:
        thread.start()

    try:
        gunicorn_process.wait()
        bluebird_process.wait()
    except KeyboardInterrupt:
        print("\nTerminating processes...")
        gunicorn_process.terminate()
        bluebird_process.terminate()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
