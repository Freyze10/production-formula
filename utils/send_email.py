import pandas as pd
from email.message import EmailMessage
from io import BytesIO
import smtplib
import ssl
import os
from typing import Union, Dict, List
from pathlib import Path


# --- Find credentials.txt relative to FG-INV root ---
def get_credentials_path(filename: str = "credentials.txt") -> Path:
    """
    Returns the full path to credentials.txt located in FG-INV root.
    Works whether you run from utils/, FG-INV/, or anywhere else.
    """
    # __file__ = utils/send_email.py
    current_file = Path(__file__).resolve()           # Full path to send_email.py
    project_root = current_file.parent.parent         # Go up: utils/ → FG-INV/
    credentials_path = project_root / filename

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

    return credentials_path

def load_credentials_from_txt(file_path: str = "credentials.txt") -> dict:
    """Read key=value lines from a .txt file and return as dict."""
    credentials = {}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Credentials file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                credentials[key.strip()] = value.strip()
    return credentials


def send_email_with_excel(
    df_dict: Dict[str, pd.DataFrame],
    recipient_email: Union[str, List[str]],
    excel_fn: str,
    subject: str,
    *,
    credentials_file: str = "credentials.txt",
    sender_email: str = None,
    sender_email_pwd: str = None,
    smtp_server: str = None,
    smtp_port: int = None,
    use_ssl: bool = True,
) -> None:
    # Load from .txt file
    creds = load_credentials_from_txt(credentials_file)

    sender_email = sender_email or creds.get("SMTP_USER")
    sender_email_pwd = sender_email_pwd or creds.get("SMTP_PASSWORD")
    smtp_server = smtp_server or creds.get("SMTP_HOST")
    smtp_port = int(smtp_port or creds.get("SMTP_PORT", "465"))
    use_ssl = use_ssl if use_ssl is not None else creds.get("SMTP_USE_SSL", "true").lower() == "true"

    if not all([sender_email, sender_email_pwd, smtp_server]):
        raise ValueError("Missing SMTP credentials in file or arguments.")

    # --- Rest of the function (same as before) ---
    if isinstance(recipient_email, str):
        recipient_email = [recipient_email]

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    excel_buffer.seek(0)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_email)
    msg.set_content("Please find the attached Excel report.")

    msg.add_attachment(
        excel_buffer.read(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=excel_fn,
    )

    context = ssl.create_default_context()
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                server.login(sender_email, sender_email_pwd)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_email_pwd)
                server.send_message(msg)
    except Exception as exc:
        raise RuntimeError(f"Email failed: {exc}") from exc
    finally:
        excel_buffer.close()

    print(f"Email with <{excel_fn}> sent to {recipient_email}")

if __name__ == "__main__":
    df_dict = {
        "Sales": pd.DataFrame({"Item": ["A", "B"], "Qty": [10, 20]}),
        "Summary": pd.DataFrame({"Total": [30]})
    }

    send_email_with_excel(
        df_dict,
        recipient_email="bjabillanoza@gmail.com",
        excel_fn="report.xlsx",
        subject="Monthly Report",
        credentials_file="credentials.txt"  # default, can omit
    )