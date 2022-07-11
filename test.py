import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)

try:
    response = {'s': 'hui'}
    hw_list = response.get('homeworks', [])
    #hw_list = response.get('homeworks')
    logging.debug(hw_list)
    print('OK')
    print(hw_list)
except IndexError as error:
    print(1)
except KeyError as error:
    print(2)
except Exception as error:
    print(3)
