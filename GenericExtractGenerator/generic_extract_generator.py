import datetime
import time
import sys
import sqlite3
import csv
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase


DATABASE = 'chinook.db'
# Logging configuration
logging.basicConfig(level=logging.INFO, filename='generic_extract_generator.log', filemode='a',
                    format='%(asctime)s | %(levelname)s | %(message)s')


# Read configuration file
def read_config(config_name):
    parameters = {}
    try:
        with open(f'config/{config_name}') as file:
            for line in file:
                fields = line.split(':')
                param = fields[0].strip()
                value = fields[1].strip()
                parameters[param] = value
            return parameters  # Return configuration file data in JSON format
    except FileNotFoundError as err:
        logging.error(err)
        raise SystemExit(f"{err}")


# Fetch data from database
def fetch_data(sql_file):
    global connection
    try:
        with open(f'sql/{sql_file}') as file:
            sql_query = file.read()
    except FileNotFoundError as err:
        logging.error(err)
        raise SystemExit(f'{err}')
    else:
        try:
            connection = sqlite3.connect(DATABASE)
        except ConnectionError as err:
            logging.error(f'Could not establish connection to database')
            raise SystemExit(f"{err}")
        else:
            cursor = connection.cursor()
            cursor.execute(sql_query)
            headers = [column[0] for column in cursor.description]  # Set headers for the file using the first row
            records = cursor.fetchall()  # Fetch table records
            return [headers] + [records]  # Return Headers and records as list of list
        finally:
            connection.close()


# Generate an extract in csv format
def generate_extract(extract_data, result_file):
    try:
        with open(f'data/{result_file}', 'w+', newline='', encoding="utf-8") as csvfile:
            obj = csv.writer(csvfile)
            logging.info(f'Saving data in {result_file}')
            # Write Headers
            obj.writerow(extract_data[0])
            # Write table records
            obj.writerows(extract_data[1])
    except Exception as err:
        logging.error(err)
        raise SystemExit(f'{result_file} could not be generated {err}')


# send email with extract
def send_email(send_from, send_to, sub, body, attachment, server="mailhost"):
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = send_from
    msg['To'] = ", ".join(send_to)

    body = f'''<html>
                <body>
                    {body}               
                </body>
             </html>'''

    msg.attach(MIMEText(body, 'html'))

    # Open file in binary mode
    try:
        with open(f'data/{attachment}', 'rb') as attached_file:
            # Add file as application/octet-stream
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attached_file.read())
    except FileNotFoundError as err:
        logging.error(err)
        raise SystemExit(f'{attachment} does not exist.')

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {attachment}",
    )

    msg.attach(part)

    smtp = smtplib.SMTP(server)
    logging.info(f'Sending email to {send_to}')
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()
    logging.info(f'{attachment} has been sent successfully.')


if __name__ == '__main__':
    try:
        config = sys.argv[1]  # Read first parameter from the command line
    except IndexError as error:
        logging.error(error)
        raise SystemExit(f"Usage: {sys.argv[0]} <Configuration File E.g. customer_extract.cfg>")
    else:
        logging.info(f'Reading configuration file {config}')
        config_parameters = read_config(config)
        logging.info(f'Fetching data from database.')
        data_list = fetch_data(config_parameters['sqlfile'])
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        extract_name = config_parameters['extractname'].replace('.csv', f'_{current_date}.csv')
        generate_extract(data_list, extract_name)
        time.sleep(5)
        logging.info(f'Generated {extract_name}')
        email_from = "tech@abc.com"
        email_to = config_parameters['email_to']
        email_cc = config_parameters['email_cc']
        subject = config_parameters['subject'] + f' - {current_date}'
        email_body = config_parameters['email_body']
        send_email(email_from, [email_to], subject, email_body, extract_name)
