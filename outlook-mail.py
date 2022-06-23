import smtplib

body = 'Subject: Subject Here .\n\n\n' + 'test'
try:
    smtpObj = smtplib.SMTP('smtp-mail.outlook.com', 587)
except Exception as e:
    print(e)
    smtpObj = smtplib.SMTP_SSL('smtp-mail.outlook.com', 465)
#type(smtpObj) 
smtpObj.ehlo()
smtpObj.starttls()
smtpObj.login('alapativamsi@outlook.com', "Nani@501") 
smtpObj.sendmail('alapativamsi@outlook.com', 'revanthgoli01@gmail.com', body) # Or recipient@outlook

smtpObj.quit()
