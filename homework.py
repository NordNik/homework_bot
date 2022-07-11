import os
import time
import requests
from telegram import Bot
from dotenv import load_dotenv
import logging
from http import HTTPStatus

load_dotenv()

logging.basicConfig(
    filename='praktikum_bot.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


class Not200ApiAnswer(Exception):
    """If status code is not 200."""

    pass


class ResponseNotType(Exception):
    """In case of non dictionary response."""

    pass


class ResponseIsEmpty(Exception):
    """In case of dictionary is empty."""

    pass


class NoVerifiedStatus(Exception):
    """If response does not include keys 'homeworks' or 'current_date'."""

    pass


def check_tokens():
    """Check if all tokens are included."""
    if (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID) is not None:
        return True
    return False


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
        raise Not200ApiAnswer(f'Response status code is not 200,\
                                 but {response.status_code}')
    return response.json()


def check_response(response):
    """Extract list of homeworks from response."""
    logging.info("start check_response function")
    if not response:
        raise ResponseIsEmpty('There is no response')
    # По совету наставника пришлось добавить такую
    # проверку, чтобы проходили тесты
    if isinstance(response, list) and len(response) == 1:
        response = response[0]
    if not isinstance(response, dict):
        raise ResponseNotType('Response is not a dictionary')
    if ('homeworks' or 'current_date') not in response:
        raise KeyError('There is no "current_date" in response')
    if 'homeworks' not in response:
        raise KeyError('There is no "homeworks" in response')
    hw_list = response.get('homeworks', [])
    if not isinstance(hw_list, list):
        raise ResponseNotType('The list of homeworks is not a list')
    return hw_list


def parse_status(homework):
    """Get list of homeworks and extract name and status from the last one."""
    # По совету наставника пришлось добавить такую
    # проверку, чтобы проходили тесты
    if isinstance(homework, list) and len(homework) == 1:
        homework = homework[0]
    if 'homework_name' not in homework:
        raise KeyError('Correct "homework_name" is not found')
    if 'status' not in homework:
        raise KeyError('Homework status is not found')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Receieved incorrect status of homework')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Send message to user."""
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f'Error while getting list of homeworks: {error}')


def main():
    """Join functions together."""
    bot = Bot(token=TELEGRAM_TOKEN)
    message = 'text'
    current_timestamp = int(time.time())
    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('current_date')
            if len(homework) != 0:
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            logging.error(f'Error while getting list of homeworks: {error}')
            error_text = 'Сбой в работе программы'
            if message != error_text:
                message = error_text
                send_message(bot, message)
            continue
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
