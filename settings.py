import base64
import os
import re
from datetime import datetime
from random import randint

import pdfkit
from pathlib import Path
from dateutil.parser import parse
from html2text import html2text
from pytz import timezone
import mysql.connector

from make_log import log_exceptions

time_out = 60
mail_time = 5 #minutes
interval = 60 #seconds
conn_data = {'host': "database-iclaim.caq5osti8c47.ap-south-1.rds.amazonaws.com",
             'user': "admin",
             'password': "Welcome1!",
             'database': 'python'}

pdfconfig = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

hospital_data = {
    'inamdar': {
        "mode": "gmail_api",
        "data": {
            "json_file": 'data/credentials_inamdar.json',
            "token_file": "data/inamdar_token.pickle"
        }
    },
    'noble': {
        "mode": "gmail_api",
        "data": {
            "json_file": 'data/credentials_noble.json',
            "token_file": "data/noble_token.pickle"
        }
    },
    'ils': {
        "mode": "graph_api",
        "data": {
            "json_file": "data/credentials_ils.json",
            "email": 'ilsmediclaim@gptgroup.co.in'
        }
    },
    'ils_dumdum': {
        "mode": "graph_api",
        "data": {
            "json_file": "data/credentials_ils.json",
            "email": 'mediclaim.ils.dumdum@gptgroup.co.in'
        }
    },
    'ils_agartala': {
        "mode": "imap_",
        "data": {
            "host": "gptgroup.icewarpcloud.in",
            "email": "billing.ils.agartala@gptgroup.co.in",
            "password": 'Gpt@2019'
        }
    },
    'ils_howrah': {
        "mode": "imap_",
        "data": {
            "host": "gptgroup.icewarpcloud.in",
            "email": "mediclaim.ils.howrah@gptgroup.co.in",
            "password": 'Gpt@2019'
        }
    },
}

time_gap_list = [i for i in hospital_data]
for i in hospital_data:
    Path(os.path.join(i, "new_attach/")).mkdir(parents=True, exist_ok=True)

def html_to_pdf(src, dst):
    with open(src, 'r') as fp:
        data = fp.read()
    data = remove_img_tags(data)
    with open(src, 'w') as fp:
        fp.write(data)
    # pdfkit.from_file(src, dst, configuration=pdfconfig)
    try:
        pdfkit.from_file(src, dst, configuration=pdfconfig)
    except:
        if os.path.exists(dst):
            pass
        else:
            raise Exception

def get_parts(part):
    if 'parts' in part:
        for i in part['parts']:
            yield from get_parts(i)
    else:
        yield part

def get_ins_process(subject, email):
    ins, process = "", ""
    q1 = "select IC from email_ids where email_ids=%s limit 1"
    q2 = "select subject, table_name from email_master where ic_id=%s"
    q3 = "select IC_name from IC_name where IC=%s limit 1"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor(buffered=True)
        cur.execute(q1, (email,))
        result = cur.fetchone()
        if result is not None:
            ic_id = result[0]
            cur.execute(q2, (ic_id,))
            result = cur.fetchall()
            for sub, pro in result:
                if 'Intimation No' in subject and email == 'claims.payment@starhealth.biz':
                    return ('big', 'settlement')
                if 'STAR HEALTH AND ALLIED INSUR04239' in subject and email == 'claims.payment@starhealth.biz':
                    return ('small', 'settlement')
                if sub in subject:
                    cur.execute(q3, (ic_id,))
                    result1 = cur.fetchone()
                    if result1 is not None:
                        return (result1[0], pro)
    return ins, process

def gen_dict_extract(key, var):
    if isinstance(var,(list, tuple, dict)):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result

def file_no(len):
    return str(randint((10 ** (len - 1)), 10 ** len)) + '_'

def clean_filename(filename):
    filename = filename.replace('.PDF', '.pdf')
    temp = ['/', ' ']
    for i in temp:
        filename = filename.replace(i, '')
    return filename

def file_blacklist(filename, **kwargs):
    fp = filename
    filename, file_extension = os.path.splitext(fp)
    ext = ['.pdf', '.htm', '.html', '.PDF', '.xls']
    if file_extension not in ext:
        return False
    if 'email' in kwargs:
        if 'ECS' in fp and kwargs['email'] == 'paylink.india@citi.com':
            return False
        if 'ecs' in fp and kwargs['email'] == 'paylink.india@citi.com':
            return False
    if fp.find('ATT00001') != -1:
        return False
    # if (fp.find('MDI') != -1) and (fp.find('Query') == -1):
    #     return False
    if (fp.find('knee') != -1):
        return False
    if (fp.find('KYC') != -1):
        return False
    if fp.find('image') != -1:
        return False
    if (fp.find('DECLARATION') != -1):
        return False
    if (fp.find('Declaration') != -1):
        return False
    if (fp.find('notification') != -1):
        return False
    if (fp.find('CLAIMGENIEPOSTER') != -1):
        return False
    if (fp.find('declar') != -1):
        return False
    return True

def remove_img_tags(data):
    p = re.compile(r'<img.*?>')
    return p.sub('', data)

def format_date(date):
    date = date.split(',')[-1].strip()
    format = '%d %b %Y %H:%M:%S %z'
    if '(' in date:
        date = date.split('(')[0].strip()
    try:
        date = datetime.strptime(date, format)
    except:
        try:
            date = parse(date)
        except:
            with open('logs/date_err.log', 'a') as fp:
                print(date, file=fp)
            raise Exception
    date = date.astimezone(timezone('Asia/Kolkata')).replace(tzinfo=None)
    format1 = '%d/%m/%Y %H:%M:%S'
    date = date.strftime(format1)
    return date

def get_utr_date_from_big(msg, **kwargs):
    try:
        def get_info(data):
            data_dict = {'utr': "", 'date': ""}
            r_list = [r"(?<=:).*(?=Date)", r"(?<=Date:).*(?=\s+Thanking you)"]
            for i, j in zip(r_list, data_dict):
                tmp = re.compile(i).search(data)
                if tmp := tmp.group().strip():
                    data_dict[j] = tmp
            return data_dict

        data = ""
        if kwargs['mode'] == 'graph_api':
            if msg['body']['contentType'] == 'html':
                data = msg['body']['content']
                data = html2text(data)
            elif msg['body']['contentType'] == 'text':
                data = msg['body']['content']


        if kwargs['mode'] == "gmail_api":
            file_list = [i for i in get_parts(msg['payload'])]
            for j in file_list:
                if j['filename'] == '' and j['mimeType'] == 'text/html':
                    data = j['body']['data']
                    data = base64.urlsafe_b64decode(data).decode()
                    if j['mimeType'] == 'text/html':
                        data = html2text(data)

        if kwargs['mode'] == 'imap_':
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    data = part.get_payload(decode=True)
                if part.get_content_type() == 'text/html':
                    data = part.get_payload(decode=True)
                    data = html2text(data)

        data_dict = get_info(data)

        q = "insert into ins_big_utr_date (`id`, `hosp`, `utr`, `date`) values (%s, %s, %s, %s);"
        params = [kwargs['id'], kwargs['hosp'], data_dict['utr'], data_dict['date']]
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(q, params)
            con.commit()
    except:
        log_exceptions(kwargs=kwargs)

def save_attachment(msg, download_folder, **kwargs):
    """
    Given a message, save its attachments to the specified
    download folder (default is /tmp)

    return: file path to attachment
    """
    att_path = []
    flag = 0
    filename = None
    file_seq = file_no(4)
    for part in msg.walk():
        z = part.get_filename()
        z1 = part.get_content_type()
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None and part.get_content_type() != 'application/octet-stream':
            continue
        flag = 1
        filename = part.get_filename()
        if filename is not None and file_blacklist(filename, email=kwargs['email']):
            if not os.path.isfile(filename):
                fp = open(os.path.join(download_folder, file_seq + filename), 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
                att_path.append(os.path.join(download_folder, file_seq + filename))
    if flag == 0 or filename is None or len(att_path) == 0:
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                filename = 'text.txt'
                fp = open(os.path.join(download_folder, filename), 'wb')
                data = part.get_payload(decode=True)
                fp.write(data)
                fp.close()
                att_path = os.path.join(download_folder, filename)
            if part.get_content_type() == 'text/html':
                filename = 'text.html'
                fp = open(os.path.join(download_folder, filename), 'wb')
                data = part.get_payload(decode=True)
                fp.write(data)
                fp.close()
                with open(os.path.join(download_folder, filename), 'r', encoding='utf-8') as fp:
                    data = fp.read()
                data = remove_img_tags(data)
                with open(os.path.join(download_folder, filename), 'w', encoding='utf-8') as fp:
                    fp.write(data)
                att_path = os.path.join(download_folder, filename)
                pass
    return att_path

def time_gap(hospital, mail_time):
    global time_gap_list
    try:
        if hospital in time_gap_list:
            q = f"SELECT date from {hospital}_mails order by STR_TO_DATE(date, '%d/%m/%Y %H:%i:%s') desc limit 1"
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(q)
                r = cur.fetchone()
                db_time = datetime.strptime(r[0], '%d/%m/%Y %H:%M:%S')
                mail_time = datetime.now() - db_time
                mail_time = round(mail_time.total_seconds()/60)+1
                time_gap_list.remove(hospital)
    except:
        log_exceptions(hospital, msg="time_gap")
    finally:
        return mail_time