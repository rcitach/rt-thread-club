import os
import sys
import time
import logging
import subprocess
from rt_thread_club import login_in_club


def execute_command(cmd_string, cwd=None, shell=True):
    """Execute the system command at the specified address."""

    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)

    stdout_str = ''
    while sub.poll() is None:
        stdout_str += str(sub.stdout.read())
        time.sleep(0.1)

    return stdout_str


def init_logger():
    log_format = " %(filename)s %(lineno)d <ignore> %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format
                        )


def main():
    username = os.environ["CLUB_USERNAME"]
    password = os.environ["CLUB_PASSWORD"]

    execute_command("sudo apt -y update && apt -y upgrade > /dev/null 2>&1")
    execute_command("sudo apt install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils > /dev/null 2>&1")
    execute_command("sudo apt-get install google-chrome-stable > /dev/null 2>&1")
    day_num = login_in_club(username, password)
    try:
        with open("sign_in_days.txt", "w") as f:
            f.write(day_num)
    except Exception as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    init_logger()
    main()
