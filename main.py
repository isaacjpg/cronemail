#! /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv


def main():

    load_dotenv()
    
    print('INFO: Executing script -->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    #Connect to DB

    try:
        conn = mysql.connector.connect(
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
        )
    except Exception as e:
        print('ERROR: Conecting to Database ',e, '-->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    cursor=conn.cursor()

    query='SELECT * FROM TRACKING WHERE ESTADO="Pendiente"'

    try:
        cursor.execute(query)
        result=cursor.fetchall()
    except Exception as e:  
        print('ERROR: Query ',e,' -->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    smtp_server = os.environ['MAIL_HOST']
    port = os.environ['MAIL_PORT']
    login=os.environ['MAIL_USERNAME']
    password = os.environ['MAIL_PASSWORD']

    try:
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        server=smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)
        server.login(login, password)
    except Exception as e:
        print('ERROR: Conecting to SMTP ',e, '-->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        server.quit()

    for d in result:
        # 0 Nro_OT
        # 1 Proceso
        # 2 Fecha Creacion
        # 3 Nventa
        # 4 Cliente
        # 5 CodProd
        # 6 Descripcion
        # 7 Fecha Entrega
        # 8 Cantidad Pedida
        # 9 Fecha Proceso
        #10 Cantidad Procesada
        #11 Nro Guia
        #12 Nro Factura
        #13 Estado
        #14 EmailTo
        #15 EmailCC

        message = MIMEMultipart("alternative")
        message["Subject"] = "{} | Estado de Ordenes de Pedido ".format(os.environ['MAIL_DEFAULT_FROM_NAME'])
        message["From"] = os.environ['MAIL_DEFAULT_FROM']
        message["To"] = d[14]
        message["Cc"] = d[15]

        html_context={
            'cliente':d[4],
            'nro_ot':d[0],
            'cod_prod':d[5],
            'desc_prod':d[6],
            'proceso':d[1],
            'from':os.environ['MAIL_DEFAULT_FROM_NAME']
        }

        # Create the plain-text and HTML version of your message
        text = """\
        Estimados {cliente},

        Se informa que la Orden Nro {nro_ot}, Producto [{cod_prod}] {desc_prod}, se encuentra en proceso {proceso}.

        Saludos cordiales,

        El equipo de {from}""".format(**html_context)

        html = """\
        <html>
        <body>
            <p>Estimados {cliente},<br>
            <br>
            Se informa que la Orden Nro <b>{nro_ot}</b>, Producto <b>[{cod_prod}] {desc_prod}</b>, se encuentra en estado <b>{proceso}</b>.<br>
            <br>
            Saludos cordiales,<br>
            <br>
            El equipo de {from}
            </p>
        </body>
        </html>
        """.format(**html_context)

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        rctp=d[14].split(',')+d[15].split(',')

        try:
            server.sendmail(os.environ['MAIL_DEFAULT_FROM'], rctp, message.as_string())
            print('OK: ','OT',d[0],' ',rctp,' ',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        except Exception as e:
            print('ERROR: Sending email ',e,' OT',d[0],' ',rctp,'-->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
        try:
            query="UPDATE TRACKING SET Estado='Enviado' WHERE Nro_OT=%s".format(d[0])
            cursor.execute(query,(d[0],))
            conn.commit()
            print('OK: Updating status ','OT',d[0],' ',rctp,' ',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        except Exception as e:
            print('ERROR: Updating status ',e,' OT',d[0],' ',rctp,'-->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            conn.rollback()

    server.quit()
    conn.close()
    print('INFO: End script -->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
if __name__ == "__main__":
    main()


        


    


    