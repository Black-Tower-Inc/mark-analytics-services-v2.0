import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import os
from dotenv import load_dotenv
from email import encoders

"""
Esta función envía un correo electrónico con un archivo adjunto a una lista de destinatarios.

type: str: Cabeza del correo.
name: str: Nombre del destinatario.
to_email: list: Lista de correos electrónicos de los destinatarios.
upload_file: str: Ruta del archivo a adjuntar.

En este caso el body del email es un mensaje en HTML y tiene un css para darle estilo al correo.

"""

def send (detalle,pasos,comentarios,to_email,upload_file,sender, subject):
    
    load_dotenv()

    msg = MIMEMultipart()

    #Alternative css
    css_style_alternative = """
        <style>
            /* Add your custom styles here */
            body {
                font-family: Arial, sans-serif;
                background-color: #222222;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
            }
            .header img {
                max-width: 200px;
                height: auto;
            }
            .content {
                background-color: #333333;
                padding: 30px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }
            .content h1 {
                color: #ffffff;
                font-size: 24px;
                margin-bottom: 20px;
            }
            .content p {
                color: #cccccc;
                font-size: 16px;
                line-height: 1.5;
            }
            .cta-button {
                display: inline-block;
                background-color: #007bff;
                color: #ffffff;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
                margin-top: 20px;
            }
        </style>
    """

    html_mensaje= f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Bug Report</title>
        <style>
            /* Add your custom styles here */
        {css_style_alternative}
        </style>
    </head>
    <body>
        <div style="background-color: #f2f2f2; padding: 20px;">
            <h1 style="text-align: center;">Mark AI Assistant bug report</h1>
            <hr>
            <p>Hola,</p>
                
            Detalles del error:
            {detalle}
            <br>  
            Pasos para reproducir el error:
            {pasos}
            <br>
            Comentarios adicionales:
            {comentarios}
            <br>
            <p>Por favor, no responda a este correo electrónico. Este mensaje ha sido enviado desde una dirección de correo electrónico no supervisada.</p>  
                
            <hr>
            <p>Kind regards,</p>
            <p>Automatic sender</p>
        </div>
    </body>
    </html>


    """

    # Attach the HTML content to the email
    msg.attach(MIMEText(html_mensaje, 'html'))

    # Attach the file
    with open(upload_file, 'rb') as file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=upload_file)
        msg.attach(part)
        

    # SMTP server configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = os.getenv("smtp_username")
    smtp_password = os.getenv("smtp_password")

    # Email configuration
    sender_email = sender
    msg['From'] = sender_email
    msg['Subject'] = subject

    #try:
    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    # Send the email
    msg['To'] = ", ".join(to_email)  # Comma-separated string of recipients
    server.sendmail(sender_email, to_email, msg.as_string())            

    server.quit()

    

    
