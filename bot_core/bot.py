import math

import requests

from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from bot_core.models import User, GroupAndSignal, Expense, Calculation, ExpenseGroup, MessageLog, Group
from django.db.models import Sum


class BotCore:

    def start_signal(self, group_id):
        group = GroupAndSignal.objects.filter(group_id=group_id).first()
        if group and group.signal == GroupAndSignal.START:
            return "Calculation has already been started. " \
                   "Before finishing the calculations we can not start all calculations again. Please finish first."
        elif group and group.signal == GroupAndSignal.FINISH:
            group.signal = GroupAndSignal.START
            group.save()
        elif not group:
            GroupAndSignal.objects.create(group_id=group_id, signal=GroupAndSignal.START)
        return False

    def finish_signal(self, group_id):
        group = GroupAndSignal.objects.filter(group_id=group_id).first()
        if group and group.signal == GroupAndSignal.FINISH:
            return "Calculation has already been finished. " \
                   "Before starting the calculations we can not finish calculations. Please start first."
        elif group and group.signal == GroupAndSignal.START:
            group.signal = GroupAndSignal.FINISH
            group.save()
        return False

    def end_calculations(self, group_id):
        group = GroupAndSignal.objects.filter(group_id=group_id)
        Expense.objects.filter(group=group.first()).delete()
        Calculation.objects.filter(group=group.first()).delete()
        ExpenseGroup.objects.filter(group_id=group_id).delete()
        group.delete()

    def get_end_calculations(self, group_id):
        group = GroupAndSignal.objects.filter(group_id=group_id).first()
        unordered_calculations = Calculation.objects.filter(group=group)
        messages = []
        calculations = unordered_calculations.values('user__username').annotate(total_debt=Sum('debt'))
        for calculation in calculations:
            messages.append(
                f"{calculation['user__username']}'s total debt is -> {'<b>{:,.3f}</b>'.format(calculation['total_debt'])}\n")
        unordered_calculations = unordered_calculations.order_by('created_date')
        if unordered_calculations:
            start_date = unordered_calculations.first().created_date.strftime("%Y-%B-%d (%H:%M)")
            end_date = unordered_calculations.last().created_date.strftime("%Y-%B-%d (%H:%M)")
            return "".join(messages), start_date, end_date

    def calculate(self, group_id):
        expense_group = ExpenseGroup.objects.filter(id=group_id).first()
        # TODO handle if there is no count object
        if not expense_group:
            return []
        expenses = Expense.objects.filter(expense_group=expense_group)
        total_expense = expenses.aggregate(total=Sum('expense_amount')).get('total')
        share = total_expense / expense_group.count
        calculations = []
        for expense in expenses:
            result = Calculation.objects.create(debt=share - expense.expense_amount, user=expense.user,
                                                group=expense.group)
            calculations.append(result)
        return calculations


class Bot(BotCore):
    NEUTRAL = 0
    START_CALCULATION = 1
    MEMBERS_COUNT = 2
    AMOUNT = 3
    USER = 4
    state = {}

    def __init__(self, token='2003844522:AAGYDJ9SjC1zvqstaQet0bogojYwpH_-I1k'):
        self.token = token
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher

    def set_webhook(self, webhook_url):
        response = requests.get(
            url=f"https://api.telegram.org/bot{self.token}/setWebhook?url={webhook_url}/")

    def log_message(self, update: Update, context: CallbackContext):
        MessageLog.objects.create(group_id=update.effective_chat.id,
                                  message=update.message.text)

    def error(self, update: Update, context: CallbackContext):
        update.message.reply_html('<b>Oops, something is wrong</b>')

    def register_members(self, update: Update, context: CallbackContext):
        group_id = update.effective_chat.id
        username = update.message.from_user.username
        user, created = User.objects.get_or_create(group_id=group_id, username=username)
        if created:
            update.message.reply_text(text=f"{user.username}, you have successfully registered")
        else:
            update.message.reply_text(text=f"User with username {user.username} is already exists.")
        return self.NEUTRAL

    def start(self, update: Update, context: CallbackContext):
        Group.objects.get_or_create(group_id=update.effective_chat.id,
                                    defaults=dict(
                                        members_count=update.effective_chat.get_member_count()))
        start_message = self.start_signal(update.effective_chat.id)
        button = ReplyKeyboardMarkup([['Start Calculations']], resize_keyboard=True)
        if start_message:
            update.message.reply_text(text=start_message, reply_markup=button)
        else:
            update.message.reply_text(text="Assalomu Alaykum, I am a bot that can handle expenses", reply_markup=button)
        return self.NEUTRAL

    def check_finish_signal(self, group_id):
        group = GroupAndSignal.objects.filter(group_id=group_id).first()
        if group and group.signal == GroupAndSignal.FINISH:
            return "Before starting the calculations we can not finish calculations. Please start first."
        return False

    def handle_calculation(self, update: Update, context: CallbackContext):
        message = 'Start Calculations'
        self.state['count'] = 0
        self.state['users'] = []
        number_suggestion_text = "Choose the number of people that shares the expense"
        chat_id = update.effective_chat.id
        group = Group.objects.filter(group_id=chat_id).first()
        inline_buttons = []
        if group:
            data = []
            for i in range(1, group.members_count):
                if len(data) == 4:
                    inline_buttons.append(data)
                    data = []
                data.append(InlineKeyboardButton(f'{i}', callback_data=i))
            inline_buttons.append(data)
        if message in update.message.text:
            update.message.reply_html(text=number_suggestion_text,
                                      reply_markup=InlineKeyboardMarkup(inline_buttons))
        return self.MEMBERS_COUNT

    def catch_count(self, update: Update, context: CallbackContext):
        query = update.callback_query
        expense_group = ExpenseGroup.objects.create(count=int(query.data), group_id=update.effective_chat.id)
        self.state['count'] = int(query.data)
        self.state['group'] = expense_group.id
        users = User.objects.filter(group_id=update.effective_chat.id)
        inline_buttons = []
        data = []
        for user in users:
            if len(data) == 4:
                inline_buttons.append(data)
                data = []
            data.append(InlineKeyboardButton(user.username, callback_data=user.id))
        inline_buttons.append(data)
        query.message.delete()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Choose the member",
                                 reply_markup=InlineKeyboardMarkup(inline_buttons), parse_mode="HTML")
        return self.AMOUNT

    def handle_member(self, update: Update, context):
        query = update.callback_query
        user_id = int(query.data)
        self.state['current_user'] = user_id
        self.state['users'].append(user_id)
        query.message.delete()
        user = User.objects.get(id=self.state['current_user'])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Type the expense of <b>{user.username}</b>",
                                 parse_mode="HTML")
        return self.USER

    def handle_amount(self, update: Update, context):
        self.state['count'] -= 1
        amount = update.message.text
        try:
            group = GroupAndSignal.objects.filter(group_id=update.effective_chat.id).first()
            Expense.objects.create(expense_group_id=self.state['group'], group=group,
                                   user_id=self.state['current_user'], expense_amount=int(amount))
        except ValueError:
            update.message.reply_text('Amount should be Integer')
            self.state['count'] += 1
            self.state['users'].remove(self.state['current_user'])
        users = User.objects.filter(group_id=update.effective_chat.id).exclude(id__in=self.state['users'])
        if self.state['count'] == 0:
            update.message.reply_html(self.one_time_calculation())
            return self.NEUTRAL
        inline_buttons = []
        data = []
        for user in users:
            if len(data) == 3:
                inline_buttons.append(data)
                data = []
            data.append(InlineKeyboardButton(user.username, callback_data=user.id))
        inline_buttons.append(data)
        update.message.reply_html(text="Choose the member", reply_markup=InlineKeyboardMarkup(inline_buttons))
        return self.AMOUNT

    def one_time_calculation(self):
        calculations = self.calculate(self.state['group'])
        if len(calculations) == 0:
            return "There is something wrong with calculating process"
        messages = []
        for calculation in calculations:
            debt = '<b>{:,.3f}</b>'.format(calculation.debt)
            messages.append(f"{calculation.user.username}'s debt is {debt} \n")
        return "".join(messages)

    def finish(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        finish_message = self.finish_signal(chat_id)
        if finish_message:
            context.bot.send_message(chat_id=chat_id, text=finish_message, reply_markup=None, parse_mode="HTML")
        else:
            data = self.get_end_calculations(chat_id)
            if data:
                messages, start_date, end_date = data
                self.end_calculations(update.effective_chat.id)
                context.bot.send_message(chat_id=chat_id, text=f"Calculation has been completed\n<b>Date:</b>\n"
                                                               f"from <b>{start_date}</b>\nto <b>{end_date}</b>",
                                         reply_markup=None, parse_mode="HTML")
                context.bot.send_message(chat_id=chat_id, text=messages, reply_markup=None, parse_mode="HTML")
        return self.START_CALCULATION
