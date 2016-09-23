import smtplib, sys, config
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

def send_mail(send_to, subject, text,
            files=None, host='smtp.gmail.com', port=587):
    assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg['From'] = config.SMTP_USERNAME
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)

    smtp = None

    try:
        smtp=smtplib.SMTP(host=host, port=port)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)

        smtp.sendmail(config.SMTP_USERNAME, send_to, msg.as_string())
    except Exception, exc:
        print( "mail failed; %s" % str(exc) ) # give a error message
    finally:
        smtp.quit()