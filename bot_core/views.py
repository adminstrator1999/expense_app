import os

import telegram
from django.http import JsonResponse
from django.views import View
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from .bot import Bot
import os

PORT = int(os.environ.get('PORT', 88))
TELEGRAM_URL = "https://api.telegram.org/bot"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "2003844522:AAGYDJ9SjC1zvqstaQet0bogojYwpH_-I1k")


# https://api.telegram.org/bot<token>/setWebhook?url=<url>/webhooks/tutorial/

class TutorialBotView(View):

    def post(self, request, *args, **kwargs):
        # tg_bot = telegram.Bot(TELEGRAM_BOT_TOKEN)
        # tg_bot.setWebhook('https://9797-185-139-137-249.ngrok.io/expense/' + TELEGRAM_BOT_TOKEN)
        bot = Bot(TELEGRAM_BOT_TOKEN)
        start_handler = CommandHandler('start', bot.start)
        finish_handler = CommandHandler('finish', bot.finish)
        register_handler = CommandHandler('register_yourself', bot.register_members)
        start_calculation = MessageHandler(Filters.regex('^(Start Calculations)$'), bot.handle_calculation)
        message_log_handler = MessageHandler(Filters.text & (~Filters.command), bot.log_message)
        calculation_handler = ConversationHandler(
            entry_points=[start_handler],
            states={
                bot.NEUTRAL: [start_calculation],
                bot.MEMBERS_COUNT: [CallbackQueryHandler(bot.catch_count)],
                bot.AMOUNT: [CallbackQueryHandler(bot.handle_member)],
                bot.USER: [MessageHandler(Filters.text, bot.handle_amount)],
                bot.START_CALCULATION: [start_handler]
            },
            fallbacks=[start_handler]
        )
        bot.dispatcher.add_handler(calculation_handler)
        bot.dispatcher.add_handler(finish_handler)
        bot.dispatcher.add_handler(register_handler)
        bot.dispatcher.add_handler(message_log_handler)
        bot.updater.start_webhook(listen="0.0.0.0",
                                  port=PORT,
                                  url_path=TELEGRAM_BOT_TOKEN)
        bot.updater.bot.setWebhook('https://expense-bot-kv-app.herokuapp.com/expense/' + TELEGRAM_BOT_TOKEN)
        # 'https://expense-bot-kv-app.herokuapp.com/'
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        bot.updater.idle()
        return JsonResponse({"ok": "POST request processed"})
