from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from cryptography.fernet import Fernet

key = b'fQs02moPjwfoZNNd2UfWMyYP78cy2GqK4Gsbl8yDMKc='
f = Fernet(key)

def encrypt(text):
    encrypted = f.encrypt(text.encode()).decode()
    return encrypted

def decrypt(text):
    if text == '':
        return ''
    decrypted = f.decrypt(text.encode()).decode()
    return decrypted

def sendResetEmail(email, name):
    sendEmail(to=email, name=name, subject = 'Reset Password', template="Email_Reset.html")

def sendInviteEmail(email, name, isAdmin):
    sendEmail(to=email, name=name, subject = 'Get Started on your Financial Model', template="Email_Invitation.html", isAdmin=isAdmin)

def sendEmail(to='d.quintana@sidesoft.com.ec',
                name='troica',
                subject="Get Started on your Financial Model",
                template="Email_Invitation.html",
                isAdmin=False):

    enc_to = encrypt(to)
    enc_name = encrypt(name)

    content = {
        'name': name,
        'enc_to': enc_to,
        'enc_name': enc_name,
    }
    to_s = [to]
    # to_s = ['fastcodespider@gmail.com', 'waelhamady@gmail.com']
    # to_s = ['josh@mightydigits.com']

    html_message = render_to_string(template, content)
    plain_message = strip_tags(html_message)
    from_email = 'Mighty Digits<Financialmodeling@mightydigits.com>'
    mail.send_mail(subject, plain_message, from_email, to_s, html_message=html_message, fail_silently=False)

    # email = mail.EmailMessage(subject, 'Body', to=['fastcodespider@gmail.com'])
    # email.send()

    # print('Sending Email')
    # mail.send_mail('Example Subject', 'Example message', 'From <Financialmodeling@mightydigits.com>', 
    #     ['d.quintana@sidesoft.com.ec', 'fastcodespider@gmail.com', 'codemissile@outlook.com'])




def sendSignupEmail(new_email, new_name):
    subject = 'A New User Signed Up!'
    from_email = 'Mighty Digits<noreply@mightydigits.com>'
    to_s = ['financialmodeling@mightydigits.com']
    template = 'Email_Signup.html'
    content = {
        'new_email': new_email,
        'new_name': new_name,
    }
    html_message = render_to_string(template, content)
    plain_message = strip_tags(html_message)
    mail.send_mail(subject, plain_message, from_email, to_s, html_message=html_message, fail_silently=False)

def sendInfoEmail(companyName):
    subject = 'A Company Completed onboarding!'
    from_email = 'Mighty Digits<noreply@mightydigits.com>'
    to_s = ['financialmodeling@mightydigits.com']
    template = 'Email_Info.html'
    content = {
        'companyName': companyName,
    }
    html_message = render_to_string(template, content)
    plain_message = strip_tags(html_message)
    mail.send_mail(subject, plain_message, from_email, to_s, html_message=html_message, fail_silently=False)