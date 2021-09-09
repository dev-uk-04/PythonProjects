"""
This program can be used to extract the data from database and send it over email.
"""

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


def read_config(config_name):
    """
    Read extract configuration file
    """
    parameters = {}
    try:
        with open(f'config/{config_name}', encoding="utf-8") as file:
            for line in file:
                fields = line.split(':')
                param = fields[0].strip()
                value = fields[1].strip()
                parameters[param] = value
            return parameters  # Return configuration file data in JSON format
    except FileNotFoundError as err:
        logging.error(err)
        raise SystemExit(err) from err


def fetch_data(sql_file):
    """
    Fetch data from database based on the sql file specified in configuration
    """
    try:
        with open(f'sql/{sql_file}', encoding="utf-8") as file:
            sql_query = file.read()
    except FileNotFoundError as err:
        logging.error(err)
        raise SystemExit(err) from err
    else:
        try:
            connection = sqlite3.connect(DATABASE)
            cursor = connection.cursor()
            cursor.execute(sql_query)
            # Set headers for the file using the first row
            headers = [column[0] for column in cursor.description]
            records = cursor.fetchall()  # Fetch table records
            return [headers] + [records]  # Return Headers and records as list of list
        except ConnectionError as err:
            logging.error('Could not establish connection to database')
            raise SystemExit(err) from err
        finally:
            # noinspection PyUnboundLocalVariable
            connection.close()


def generate_extract(extract_data, result_file):
    """
    Generate an extract in csv format
    """
    try:
        with open(f'data/{result_file}', 'w+', newline='', encoding="utf-8") as csvfile:
            obj = csv.writer(csvfile)
            logging.info('Saving data in %s', result_file)
            # Write Headers
            obj.writerow(extract_data[0])
            # Write table records
            obj.writerows(extract_data[1])
    except Exception as err:
        logging.error(err)
        raise SystemExit(f'{result_file} could not be generated {err}') from err


def send_email(send_from, send_to, sub, body, attachment):
    """
    send email with extract as an attachment. the recipient, subject details
    are coming from configuration(.cfg) file.
    """
    server = "mailhost"
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
        raise SystemExit(f'{attachment} does not exist.') from err

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {attachment}",
    )

    msg.attach(part)

    smtp = smtplib.SMTP(server)
    logging.info('Sending email to %s', send_to)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()
    logging.info('%s has been sent successfully.', attachment)


if __name__ == '__main__':
    try:
        config = sys.argv[1]  # Read first parameter from the command line
    except IndexError as error:
        logging.error(error)
        raise SystemExit(f'''Usage: {sys.argv[0]} <Configuration File E.g. customer_extract.cfg>'''
                         ) from error
    else:
        logging.info('Reading configuration file %s', config)
        config_parameters = read_config(config)
        logging.info('Fetching data from database.')
        data_list = fetch_data(config_parameters['sqlfile'])
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        extract_name = config_parameters['extractname'].replace('.csv', f'_{current_date}.csv')
        generate_extract(data_list, extract_name)
        time.sleep(5)
        logging.info('Generated %s', extract_name)
        EMAIL_FROM = "tech@abc.com"
        email_to = config_parameters['email_to']
        email_cc = config_parameters['email_cc']
        subject = config_parameters['subject'] + f' - {current_date}'
        email_body = config_parameters['email_body']
        # send_email(EMAIL_FROM, [email_to], subject, email_body, extract_name)
