import requests,time,os,sys,json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def get_json(search_job):
    url = "https://mitrakeluarga.jobseeker.software/vacancy/ajaxFilterVacancy/0"
    payload = f"search_jobs={search_job}"
    headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-US,en;q=0.9,id;q=0.8',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': 'ci_session=m81npsa3q9v69gc69hcpneitkkcgdci0; ci_session=m81npsa3q9v69gc69hcpneitkkcgdci0',
    'origin': 'https://mitrakeluarga.jobseeker.software',
    'priority': 'u=1, i',
    'referer': 'https://mitrakeluarga.jobseeker.software/vacancy?location=undefined',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    'x-kl-kfa-ajax-request': 'Ajax_Request',
    'x-requested-with': 'XMLHttpRequest'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def main():
    data = get_json(os.getenv('SEARCH_JOB'))
    
    if(data['count'] == 0):
        return {
            'status' : False,
        }
    
    html = data['vacancy']

    soup = BeautifulSoup(html, 'html.parser')

    # open history.json 
    history = ''
    try:
        with open('history.json', 'r') as file:
            history = file.read()
    except:
        with open('history.json', 'w') as file:
            file.write('')

    # check if history.json is empty
    if(history == ''):
        history = '[]'

    # convert history to list
    history = eval(history)


    # get cards
    cards = soup.find_all('div', class_='col-md-6 mt-1 mb-3')
    listData = []
    for card in cards:
        # get lokasi
        lokasi = card.find('span', style="font-size: 15px; color: #808080;").text


        # get title anchor
        titleAchor = card.select_one('p > a')
        title = titleAchor.text
        linkTitle = titleAchor['href']

        # get tanggal
        tanggal = card.find('small').text.strip()

        # check if data already in history
        duplicate = False
        for h in history:
            if(h['linkTitle'] == linkTitle):
                duplicate = True
                break

        if(duplicate):
            continue

        # put data to history
        history.append({
            'lokasi' : lokasi,
            'title' : title,
            'linkTitle' : linkTitle,
            'tanggal' : tanggal
        })

        # put data to list
        listData.append({
            'lokasi' : lokasi,
            'title' : title,
            'linkTitle' : linkTitle,
            'tanggal' : tanggal
        })

    # write history to history.json
    with open('history.json', 'w') as file:
        file.write(json.dumps(history))

    return {
        'status' : True,
        'data' : {
            'total' : data['count'],
            'listData' : listData
        }
    }

def telegram_bot_sendtext(bot_message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    bot_chat = os.getenv('TELEGRAM_CHAT_ID')

    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chat + '&parse_mode=Markdown&text=' + bot_message + '&disable_web_page_preview=true'
    response = requests.get(send_text)

    return response.json()

import sys

if __name__ == "__main__":
    load_dotenv()
    print("Starting program...")
    print("Checking...")
    try:
        while True:
            try:
                result = main()
                if(result['status']):
                    total = result['data']['total']
                    listData = result['data']['listData']
                    message = f"Ada {total} lowongan baru\n"
                    for data in listData:
                        message += f"{data['title']} ({data['lokasi']})\n{data['tanggal']}\n{data['linkTitle']}\n\n"
                    
                    # send message to telegram only if there is new data
                    if(len(listData) > 0):
                        telegram_bot_sendtext(message)
                time.sleep(60*5)
            except Exception as e:
                # send error message to telegram
                telegram_bot_sendtext(f"Hey ada error nih\n{e}")
                time.sleep(60*2)
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting program.")
        sys.exit(0)