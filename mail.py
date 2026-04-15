import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def send_prescription_mail(
    gmail_user: str,
    gmail_password: str,
    to_email: str,
    cc_emails: list,
    subject: str,
    body: str,
    pdf_path: str
):
    """
    Send prescription PDF via Gmail SMTP SSL.

    Args:
        gmail_user     : Sender Gmail address (from Streamlit secrets GMAIL_USER)
        gmail_password : Gmail App Password    (from Streamlit secrets GMAIL_PASSWORD)
        to_email       : Recipient email address
        cc_emails      : List of CC email addresses (can be empty list)
        subject        : Email subject line
        body           : Plain text email body
        pdf_path       : Absolute or relative path to the PDF file to attach

    Returns:
        (success: bool, error_message: str or None)
    """
    if not gmail_user or not gmail_password:
        return False, "GMAIL_USER or GMAIL_PASSWORD not configured in Streamlit secrets."

    if not os.path.exists(pdf_path):
        return False, f"PDF file not found at path: {pdf_path}"

    try:
        msg = MIMEMultipart()
        msg['From']    = gmail_user
        msg['To']      = to_email
        msg['Subject'] = subject

        if cc_emails:
            msg['Cc'] = ", ".join(cc_emails)

        # Attach body
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        with open(pdf_path, 'rb') as f:
            pdf_part = MIMEApplication(f.read(), _subtype='pdf')
            pdf_part.add_header(
                'Content-Disposition', 'attachment',
                filename=os.path.basename(pdf_path)
            )
            msg.attach(pdf_part)

        # All recipients = To + CC
        all_recipients = [to_email] + (cc_emails if cc_emails else [])

        # Send via Gmail SSL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, all_recipients, msg.as_string())

        return True, None

    except smtplib.SMTPAuthenticationError:
        return False, (
            "Gmail authentication failed. "
            "Please make sure you are using a Gmail App Password, not your regular account password. "
            "Generate one at: https://myaccount.google.com/apppasswords"
        )
    except smtplib.SMTPRecipientsRefused as e:
        return False, f"Recipient email refused: {e}"
    except Exception as e:
        return False, str(e)
