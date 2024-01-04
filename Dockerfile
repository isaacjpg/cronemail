FROM python:3.10
RUN apt-get update && apt-get -y install cron vim
WORKDIR /app
RUN pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
COPY main.py /app/main.py
COPY main_image.py /app/main_image.py
COPY .env /app/.env
#COPY despacho.png /app/despacho.png
#COPY ingreso_ot.png /app/ingreso_ot.png
#COPY planificacion.png /app/planificacion.png
RUN touch /var/log/cron.log

RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

RUN echo $PYTHONPATH

# run crond as main process of container
CMD cron && tail -f /var/log/cron.log