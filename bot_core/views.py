import os

from django.http import JsonResponse
from django.views import View
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from .bot import Bot

TELEGRAM_URL = "https://api.telegram.org/bot"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "2003844522:AAGYDJ9SjC1zvqstaQet0bogojYwpH_-I1k")


# https://api.telegram.org/bot<token>/setWebhook?url=<url>/webhooks/tutorial/

class TutorialBotView(View):

    def post(self, request, *args, **kwargs):
        bot = Bot()
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
        bot.updater.start_polling()
        return JsonResponse({"ok": "POST request processed"})
