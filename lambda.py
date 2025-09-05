import json
import requests
import PyPDF2
from bs4 import BeautifulSoup
import telebot
import os
from datetime import datetime, timedelta

bot_token = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(bot_token)
regioni = ['valle_d_aosta', 'piemonte', 'lombardia']
province = ['AO', 'TO', 'VC', 'PV', 'MI', 'NO']

def bot_send_message(msg):
    bot.send_message(chat_id=xxxxxxxxx, text=msg)

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        if last not in s:
            return s[start:]
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ''
        
def get_my_dates():
    today_date = datetime.now().date()
    tomorrow_date = today_date + timedelta(days=1)
    today = today_date.strftime('%d/%m/%Y')
    tomorrow = tomorrow_date.strftime('%d/%m/%Y')
    return today, tomorrow, today_date.strftime('%A')


def read_pdf_from_web(pdf_link, day):
    today = day[0]
    tomorrow = day[1]
    url = 'https://www.poliziadistato.it' + pdf_link['href']
    response = requests.get(url)
    local_filename = '/tmp/temp_pdf.pdf'
    
    with open(local_filename, 'wb') as pdf_file:
        pdf_file.write(response.content)

    with open(local_filename, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        text = ''
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    
    autovelox_today = find_between(text, today, tomorrow).replace(' /', '').strip()
    my_list = autovelox_today.split('\n')
    my_roads = [x for x in my_list if x[-2:] in province]
    return my_roads
    
    
def lambda_handler(event, context):
    url = 'https://www.poliziadistato.it/articolo/autovelox-e-tutor-dove-sono'
    response = requests.get(url)
    if response.status_code == 200:
        day = get_my_dates()
        soup = BeautifulSoup(response.text, 'html.parser')
        msg = f'AUTOVELOX \n{day[2].upper()} {day[0]}:\n\n'
        for regione in regioni:
            file_name = regione + '.pdf'
            pdf_link = soup.find('a', href=lambda href: (href and href.endswith(file_name)))
            if pdf_link:
                roads = read_pdf_from_web(pdf_link, day)
                if roads:
                    msg = msg + f'{regione}\n' + '\n'.join(roads) + '\n\n'
        bot_send_message(msg)
    else:
        bot_send_message('Error')
