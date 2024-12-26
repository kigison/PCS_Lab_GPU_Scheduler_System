import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid
from config import SMTP_Config

class EmailSender:
    def __init__(self, sender_email=None, sender_password=None):
        """
        Initialize the EmailSender class with the sender's credentials.

        :param sender_email: Sender's email address (default from SMTP_Config)
        :param sender_password: Sender's email password (default from SMTP_Config)
        """
        self.sender_email = sender_email or SMTP_Config.SENDER_EMAIL
        self.sender_password = sender_password or SMTP_Config.PASSWORD

    def send_RAW_email(self, subject, body, receiver_emails, cc_emails=None):
        """
        Send an email with the specified subject, body, and recipients.

        :param subject: Email subject
        :param body: Email body content
        :param receiver_emails: List of main recipient email addresses
        :param cc_emails: List of CC email addresses (optional)
        :return: Dictionary with failed recipients and error messages, if any
        """
        cc_emails = cc_emails or []

        # Add the automatic reply disclaimer to the beginning of the body
        disclaimer = "This is an automated email sent by the PCS Lab GPU Scheduler System (gpusched.iottalk.tw). Please do not reply.\n\n\n"

        # Create email message
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = ", ".join(receiver_emails)
        message["Cc"] = ", ".join(cc_emails)
        message["Subject"] = subject
        message.attach(MIMEText(disclaimer + body, "plain"))
        

        # Combine recipients
        all_recipients = receiver_emails + cc_emails

        # Send email via SMTP
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_password)
                response = server.sendmail(self.sender_email, all_recipients, message.as_string())
                
                # Return any errors for failed recipients
                if response:
                    failed_recipients = "\n".join([f"{recipient}: {error}" for recipient, error in response.items()])
                    print(f"Failed to send email to some recipients:\n{failed_recipients}")
                    return False
                # print(f"Email sent successfully. Receiver emails: {receiver_emails}. CC emails: {cc_emails}")
                return True

        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def send_test_msg(self, receiver_emails, cc_emails=None):
        """
        Send a test email to verify the setup.

        :param receiver_emails: List of main recipient email addresses
        :param cc_emails: List of CC email addresses (optional)
        """
        subject = "PCS Lab GPU Scheduler System Test Email"
        body = "This is a test email send from PCS Lab GPU Scheduler System!"
        return self.send_RAW_email(subject, body, receiver_emails, cc_emails)
    
    def send_login_notify(self, name, username, receiver_email, datetime, ip_address):
        """
        Send a notification email to the user about a login event.

        :param name: User's full name
        :param username: User's username
        :param receiver_email: Email address of the recipient
        :param datetime: Date and time of the login event (datetime.datetime.now())
        :param ip_address: User login IP
        :return: The result of the email sending attempt
        """
        subject = "Login Alert: PCS Lab GPU Scheduler System"
        body = f"Hello {name} ({username}),\n\nWe detected a login to your account at {datetime} from IP address {ip_address}. \nIf this wasn't you, please reset your password immediately to secure your account."
        return self.send_RAW_email(subject, body, [receiver_email])
    
    def send_pwd_change_notify(self, name, username, receiver_email, datetime, ip_address):
        """
        Send a notification email to the user about a password change.

        :param name: User's full name
        :param username: User's username
        :param receiver_email: Email address of the recipient
        :param datetime: Date and time of the password change (datetime.datetime.now())
        :return: The result of the email sending attempt
        """
        subject = "Password Change Alert: PCS Lab GPU Scheduler System"
        body = f"Hello {name} ({username}),\n\nYour password was changed successfully at {datetime} from IP address {ip_address}. \nIf you did not initiate this change, please reset your password immediately to prevent unauthorized access."
        return self.send_RAW_email(subject, body, [receiver_email])
    
    def send_new_pwd(self, name, username, receiver_email, password):
        """
        Send a notification email to the user with their new password after an admin reset.

        :param name: User's full name
        :param username: User's username
        :param receiver_email: Email address of the recipient
        :param password: The new password set by the admin
        :return: The result of the email sending attempt
        """
        subject = "Your Password Has Been Reset: PCS Lab GPU Scheduler System"
        body = f"Hello {name} ({username}),\n\nYour password has been reset by an administrator.\n\nYour new password is: {password}\n\nPlease log in and change your password as soon as possible for security reasons."
        return self.send_RAW_email(subject, body, [receiver_email])


if __name__ == "__main__":
    print("Send test email~")
    email_sender = EmailSender()
    result = email_sender.send_test_msg(receiver_emails=["kcchuang88@gmail.com"])
    print(result)