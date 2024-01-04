#! /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv


def main():

    load_dotenv()
    
    #print('INFO: Executing script -->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
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
        #16 Orden de Compra
        #17 Unidad de Medida

        # message = MIMEMultipart("alternative")
        # message["Subject"] = "{} | Estado de Ordenes de Pedido ".format(os.environ['MAIL_DEFAULT_FROM_NAME'])
        # message["From"] = os.environ['MAIL_DEFAULT_FROM']
        # message["To"] = d[14]
        # message["Cc"] = d[15]

        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = "{} | Estado de Ordenes de Pedido ".format(os.environ['MAIL_DEFAULT_FROM_NAME'])
        msgRoot['From'] = os.environ['MAIL_DEFAULT_FROM']
        msgRoot['To'] = d[14]
        msgRoot['Cc'] = d[15]
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)


        html_context={
            'o_compra':d[16] if d[16] else '---',
            'nro_factura':d[12] if d[12] else '---',
            'cant_facturada':d[10],
            'pedido':d[8],
            'unidad_medida':d[17] if d[17] else '---',
            'cliente':d[4],
            'nro_ot':d[0],
            'cod_prod':d[5],
            'desc_prod':d[6],
            'proceso':d[1],
            'from':os.environ['MAIL_DEFAULT_FROM_NAME']
        }

        if d[1]=='Facturado':
            html_factura = "<br>La factura <b>{nro_factura}</b> se encuentra en ruta con <b>{cant_facturada}</b> de <b>{pedido} {unidad_medida}</b>.<br>".format(**html_context)

            texto_factura = "La factura {nro_factura} se encuentra en ruta con {cant_facturada} de {pedido} {unidad_medida}.".format(**html_context)
        else:
            html_factura=""
            texto_factura=""
        
        html_context['texto_factura']=texto_factura
        html_context['html_factura']=html_factura

        # Create the plain-text and HTML version of your message
        text = """\
        Estimados {cliente},

        Su Orden de compra {o_compra}, del producto {desc_prod}, Orden de Trabajo {nro_ot}, está actualmente se encuentra en proceso de {proceso}.

        {texto_factura}

        Ante cualquier duda referente a su Orden favor contactarse con usc@imiflex.cl.

        """.format(**html_context)

        html = """\
        <html>
            <body>
                <p>Estimados {cliente},
                    <br>
                    <br>
                    Su Orden de Compra <b>{o_compra}</b>, del producto {desc_prod}, Orden de Trabajo <b>{nro_ot}</b>, está actualmente en proceso de <b>{proceso}</b>.
                    <br>
                    {html_factura}
                    <br>
                    Ante cualquier duda referente a su Orden favor contactarse con <a href="mailto:usc@imiflex.cl">usc@imiflex.cl</a>.
                    <br>
                    <br>
                    <img src="cid:image1">
                </p>
            </body>
        </html>
        """.format(**html_context)



        msgAlternative.attach(MIMEText(text, 'plain'))
        msgAlternative.attach(MIMEText(html, 'html'))

        try:

            #Open de files
            if d[1]=='Facturado':
                fp = open('despacho.png', 'rb')
            elif d[1]=='Planificado':
                fp = open('planificacion.png', 'rb')
            else:
                fp = open('ingreso_ot.png', 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()

            # Define the image's ID as referenced above
            msgImage.add_header('Content-ID', '<image1>')
            msgRoot.attach(msgImage)
        except Exception as e:
            print('ERROR: Attaching image ',e,' -->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


        # Turn these into plain/html MIMEText objects
        # part1 = MIMEText(text, "plain")
        # part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        # message.attach(part1)
        # message.attach(part2)

        rctp=d[14].split(',')+d[15].split(',')

        try:
            server.sendmail(os.environ['MAIL_DEFAULT_FROM'], rctp, msgRoot.as_string())
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
    #print('INFO: End script -->',datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
if __name__ == "__main__":
    main()


        


    


    