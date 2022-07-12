import os
import time
import requests
from telegram import Bot
from dotenv import load_dotenv
import logging
from http import HTTPStatus

from exceptions import Not200ApiAnswer, ResponseNotType, ResponseIsEmpty


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


bot = Bot(token=TELEGRAM_TOKEN)


def check_tokens():
    """Check if all tokens are included."""
    ans = all([PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID])
    return ans


def get_api_answer(current_timestamp):
    """Get homeworks for certain time."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Response status code is not 200,\
            but {response.status_code}')
        raise Not200ApiAnswer(f'Response status code is not 200,\
            but {response.status_code}')
    if not isinstance(response.json(), dict):
        logging.error('Response.json() is not a dictionary')
        raise ResponseNotType('Response.json() is not a dictionary')
    return response.json()


def check_response(response):
    """Extract list of homeworks from response."""
    logging.info("start check_response function")
    if not response:
        logging.error('There is no response')
        raise ResponseIsEmpty('There is no response')
    # По совету наставника пришлось добавить такую
    # проверку, чтобы проходили тесты
    if isinstance(response, list) and len(response) == 1:
        response = response[0]
    if not isinstance(response, dict):
        logging.error('Response is not a dictionary')
        raise ResponseNotType('Response is not a dictionary')
    if ('homeworks' or 'current_date') not in response:
        logging.error('There is no "current_date" in response')
        raise KeyError('There is no "current_date" in response')
    if 'homeworks' not in response:
        logging.error('There is no "homeworks" in response')
        raise KeyError('There is no "homeworks" in response')
    hw_list = response.get('homeworks', [])
    if not isinstance(hw_list, list):
        logging.error('The list of homeworks is not a list')
        raise ResponseNotType('The list of homeworks is not a list')
    return hw_list


def parse_status(homework):
    """Get list of homeworks and extract name and status from the last one."""
    # По совету наставника пришлось добавить такую
    # проверку, чтобы проходили тесты
    if isinstance(homework, list) and len(homework) == 1:
        homework = homework[0]
    if 'homework_name' not in homework:
        logging.error('There is no homework_name in list of homeworks')
        raise KeyError('Correct "homework_name" is not found')
    if 'status' not in homework:
        logging.error('There is no status in list of homeworks')
        raise KeyError('Homework status is not found')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Incorrect status of homeworks')
        raise KeyError('Receieved incorrect status of homework')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Send message to user."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info("message has sended")
    except Exception as error:
        logging.error(f'Error while getting list of homeworks: {error}')


def main():
    """Join functions together."""
    logging.basicConfig(
        filename='praktikum_bot.log',
        filemode='w',
        format=('%(asctime)s - %(name)s - %(levelname)s\
                - %(lineno)s - %(message)s'),
        level=logging.DEBUG)
    message = 'text'
    current_timestamp = int(time.time())
    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('current_date')
            if len(homework) != 0:
                message = parse_status(homework[0])
                print(message)
                send_message(bot, message)
        except Exception:
            error_text = 'Сбой в работе программы'
            if message != error_text:
                message = error_text
                print(message)
                send_message(bot, message)
            continue
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
