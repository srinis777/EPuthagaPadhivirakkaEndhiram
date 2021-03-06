import logging
import os
import re

from telegram import TelegramError
from telegram.ext import Updater
from telegram.ext import CommandHandler
import ragasiya_padhivirakkam

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_document(asin, status, bot, chat_id):
    """
    send document to the user
    :param asin:
    :param status:
    :param bot:
    :param chat_id:
    :return:
    """
    status = ragasiya_padhivirakkam.get_book_from_local(asin, status)
    if 'Error:' in status or not os.path.exists(status):
        bot.send_message(chat_id=chat_id, text='Sorry!!! Could not process download and the error is {}'
                         .format(status))
        return
    try:
        msg = bot.sendDocument(chat_id=chat_id, document=open(status.strip(), 'rb'), timeout=30000)
        logger.info("Msg FileID: " + msg.document.file_id)
    except Exception as e:
        logger.critical('cannot send document {}'.format(status.strip()))
        logger.critical(e.message)
    else:
        logger.info('successfully sent document {}'.format(status.strip()))
    finally:
        os.remove(status.strip())


def start(bot, update, args):
    """
    start listening updates from telegram
    :param bot:
    :param update:
    :param args:
    :return:
    """
    try:
        asin = args[0]
        chat_id = update.message.chat_id
        if len(asin) != 10:
            bot.send_message(chat_id=chat_id, text="Please provide proper 10 digit book id")
            return
        pattern = re.compile('^B[a-zA-Z0-9]+$')
        gr = pattern.match(asin)
        if gr is None:
            bot.send_message(chat_id=chat_id, text="Please provide proper 10 digit book id")
            return
        bot.send_message(chat_id=chat_id, text="Initiating download. Please relax for some time")
        status = ragasiya_padhivirakkam.download_book(asin)
        logger.info(' Status of book downloader: {}---'.format(status))
        logger.info('Does book Local Path {}: '.format(str(os.path.exists(status))))
        if 'Error:' in status or not os.path.exists(status):
            logger.info('Sending err msg back to user')
            bot.send_message(chat_id=chat_id, text='Sorry!!! Could not process download and the error is {}'.
                             format(status), timeout=1500)
        else:
            logger.info('Replying back to user')
            try:
                update.message.reply_text("Book Found!!! Please wait for some more time while your book is on the way",
                                    timeout=1500)
                send_document(asin, status, bot, chat_id)
            except Exception as e:
                logger.info(e.message)
                bot.send_message(chat_id=chat_id, text='Book Found!!! Please wait for some more time'
                                                    ' while your book is on the way')
                send_document(asin, status, bot, chat_id)
    except TelegramError as e:
        logger.info("TELEGRAMException " + e.message)
        start(bot, update, args)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(token='668051538:AAEIRiZdSX3qXCjCE2xLRr3mYTQ4rUG0uno')
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('bid', start, pass_args=True)
    dispatcher.add_handler(start_handler)
    # log all errors
    dispatcher.add_error_handler(error)
    # Start the Bot
    updater.start_polling()


if __name__ == '__main__':
    main()
