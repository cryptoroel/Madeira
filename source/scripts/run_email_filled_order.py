import sys
sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

import os
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from api.binance_api import make_wallet_info_order_history, get_human_time
from config import gmail_passwd

def send_email(body):
    subject = "CryptoMadeira"
    sender = "roel.heremans@gmail.com"
    recipients = ["cryptoroel@protonmail.com", "roel.heremans@gmail.com"]
    password = gmail_passwd.email_psswd

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp_server.login(sender, password)
    smtp_server.sendmail(sender, recipients, msg.as_string())
    smtp_server.quit()



if __name__ == "__main__":

    dir_out = '/home/rheremans/Repos/CryptoMadeira/source/outputs/mail_sent_status/'
    now = datetime.today()

    ####################################################################################################################
    symbol = 'BTCUSDT'
    file_out = f"{symbol}_lastorder.json"
    my_json = make_wallet_info_order_history(symbol)
    last_order = my_json[-1]

    if not os.path.exists(dir_out):
        os.makedirs(dir_out)

    if not os.path.isfile(os.path.join(dir_out, file_out)):
        with open(os.path.join(dir_out, file_out), 'w') as outfile:
            json.dump(last_order, outfile)

    with open(os.path.join(dir_out, file_out)) as json_file:
        my_last_order_filled = json.load(json_file)

    if my_last_order_filled['orderId'] != last_order['orderId']:
        with open(os.path.join(dir_out, file_out), 'w') as outfile:
            json.dump(last_order, outfile)

        mail_content = f"Hi Roel,\nA new transaction has been taking place on Binance. "\
                       f"\n\nSymbol: {symbol}"\
                       f"\n        {last_order['side']}"f"\nstatus: {last_order['status']} at {get_human_time(last_order['updateTime'])}"\
                       f"\namount: {last_order['executedQty']}"\
                       f"\nat price of: {float(last_order['cummulativeQuoteQty'])/float(last_order['executedQty'])}"\
                       f"\npayed: {last_order['cummulativeQuoteQty']}"

        send_email(mail_content)

    ####################################################################################################################
    symbol = 'ETHEUR'
    file_out = f"{symbol}_lastorder.json"
    my_json = make_wallet_info_order_history(symbol)
    last_order = my_json[-1]
    if not os.path.exists(dir_out):
        os.makedirs(dir_out)
    if not os.path.isfile(os.path.join(dir_out, file_out)):
        with open(os.path.join(dir_out, file_out), 'w') as outfile:
            json.dump(last_order, outfile)
    with open(os.path.join(dir_out, file_out)) as json_file:
        my_last_order_filled = json.load(json_file)
    if my_last_order_filled['orderId'] != last_order['orderId']:
        with open(os.path.join(dir_out, file_out), 'w') as outfile:
            json.dump(last_order, outfile)
        mail_content = f"Hi Roel,\nA new transaction has been taking place on Binance. " \
                       f"\n\nSymbol: {symbol}" \
                       f"\n        {last_order['side']}"f"\nstatus: {last_order['status']} at {get_human_time(last_order['updateTime'])}" \
                       f"\namount: {last_order['executedQty']}" \
                       f"\nat price of: {float(last_order['cummulativeQuoteQty']) / float(last_order['executedQty'])}" \
                       f"\npayed: {last_order['cummulativeQuoteQty']}"
        send_email(mail_content)