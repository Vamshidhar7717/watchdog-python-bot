import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import smtplib
from email.message import EmailMessage
import pandas as pd

import psutil
import time

MONITORED_SCRIPT = "bot.py"
CHECK_INTERVAL = 10  # seconds

def is_bot_running(script_name):
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if "python" in proc.info["name"].lower() and script_name in proc.info["cmdline"]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def get_error_records_from_csv(file_path: str, status_column: str = "Status", sep: str = ","):
    """
    Reads a CSV file and returns rows where the status column contains 'error' (case-insensitive).

    :param file_path: Path to the CSV file
    :param status_column: Column name to check for the keyword 'error'
    :param sep: CSV separator (default is comma)
    :return: DataFrame containing matching error rows
    """
    try:
        df = pd.read_csv(file_path, sep=sep)
        if status_column not in df.columns:
            raise KeyError(f"Column '{status_column}' not found in CSV columns: {df.columns.tolist()}")
        error_rows = df[df[status_column].str.contains("error", case=False, na=False)]
        return error_rows
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return pd.DataFrame()

def send_email_alert(subject: str, message: str, to_email: str):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    from_email = "nsaopen@orthomedstaffing.com"
    password = "OMS@dev1!"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(message)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

class ReselectionFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)
        if filename == "reselectionoutput.csv":
            print(f"[INFO] Detected modification in: {event.src_path}")
            run_bot()


def run_bot():
    error_df = get_error_records_from_csv("watch_folder/reselectionoutput.csv", status_column="Status", sep=",")
    print("Error detected in reselectionoutput.csv:")
    if not error_df.empty:
        print(error_df)
    send_email_alert("Error occurred in reslectionoutput.csv", "We encountered an error", "vgangula@orthomedstaffing.com")


if __name__ == "__main__":
    watch_path = "./watch_folder"
    os.makedirs(watch_path, exist_ok=True)

    print(f"[WATCHING] Monitoring folder: {os.path.abspath(watch_path)}")

    event_handler = ReselectionFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watch_path, recursive=False)
    send_mail_triggerd = False

    try:
        observer.start()
        while True:
            time.sleep(1)
            if is_bot_running(MONITORED_SCRIPT):
                print(f"{MONITORED_SCRIPT} is running.")
                send_mail_triggerd = False
            else:
                print(f"{MONITORED_SCRIPT} is NOT running!")
                if send_mail_triggerd == False:
                    print("mail send triggered")
                    send_email_alert("Error occurred, bot stopped running", "We encountered an error", "vgangula@orthomedstaffing.com")
                send_mail_triggerd = True
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n[EXIT] Stopping observer.")
        observer.stop()
    observer.join()
