import smtplib
import ssl
from email.message import EmailMessage
from io import BytesIO
from pathlib import Path
from typing import Union, List

import pandas as pd


# --- Find credentials.txt relative to FG-INV root ---
def get_credentials_path(filename: str = "credentials.txt") -> Path:
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    credentials_path = project_root / filename

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
    return credentials_path


def load_credentials_from_txt(file_path: str = "credentials.txt") -> dict:
    credentials_path = get_credentials_path(file_path)
    creds = {}
    with open(credentials_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()
    return creds


def send_email_with_excel_bytes(
        excel_bytes: bytes,
        filename: str,
        recipient_email: Union[str, List[str]],
        subject: str,
        body: str = "Please find the attached Excel file.",
        *,
        credentials_file: str = "credentials.txt",
        sender_email: str = None,
        sender_email_pwd: str = None,
        smtp_server: str = None,
        smtp_port: int = None,
        use_ssl: bool = True,
) -> None:
    """
    Send an email with a pre-generated Excel file (as bytes).

    Args:
        excel_bytes: The .xlsx file content as bytes (e.g. from BytesIO.getvalue())
        filename: Name of the attachment (e.g. "Formulas_Jan2025.xlsx")
        recipient_email: Single email or list of emails
        subject: Email subject
        body: Email body text
    """
    creds = load_credentials_from_txt(credentials_file)

    sender_email = sender_email or creds.get("SMTP_USER")
    sender_email_pwd = (sender_email_pwd or creds.get("SMTP_PASSWORD", "")).replace(" ", "")
    smtp_server = smtp_server or creds.get("SMTP_HOST")
    smtp_port = int(smtp_port or creds.get("SMTP_PORT", "465"))
    use_ssl = use_ssl if use_ssl is not None else creds.get("SMTP_USE_SSL", "true").lower() == "true"

    if not all([sender_email, sender_email_pwd, smtp_server]):
        raise ValueError("Missing SMTP credentials. Check credentials.txt")

    if isinstance(recipient_email, str):
        recipient_email = [recipient_email]

    # Compose email
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_email)
    msg.set_content(body)

    # Attach the pre-generated Excel file
    msg.add_attachment(
        excel_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

    # Send email
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

        print(f"Email sent successfully to: {', '.join(recipient_email)}")
        print(f"Attachment: {filename} ({len(excel_bytes):,} bytes)")

    except Exception as exc:
        raise RuntimeError(f"Failed to send email: {exc}") from exc


# --- Test (optional) ---
if __name__ == "__main__":
    # Simulate your temp Excel file
    sample_df = pd.DataFrame({"Test": [1, 2, 3]})
    buffer = BytesIO()
    sample_df.to_excel(buffer, index=False)
    buffer.seek(0)

    send_email_with_excel_bytes(
        excel_bytes=buffer.getvalue(),
        filename="prod_formula.xlsx",
        recipient_email="ppsycho109@gmail.com",
        subject="Monthly Report",
        body="Please find the attached Excel report."
    )