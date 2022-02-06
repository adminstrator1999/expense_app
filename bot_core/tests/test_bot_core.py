from django.db.models import Sum
from django.test import TestCase
from bot_core.models import GroupAndSignal, Calculation, ExpenseGroup, Expense, User
from bot_core.bot import BotCore


class GroupAndSignalTestCase(TestCase):

    def setUp(self) -> None:
        GroupAndSignal.objects.create(group_id=1, signal=GroupAndSignal.START)
        GroupAndSignal.objects.create(group_id=2, signal=GroupAndSignal.FINISH)

    def test_start(self):
        bot = BotCore()
        message = bot.start_signal(1)
        bot.start_signal(2)
        bot.start_signal(3)
        self.assertEqual(message, "Calculation has already been started. "
                                  "Before finishing the calculations we can not start all calculations again. "
                                  "Please finish first.")
        self.assertEqual(GroupAndSignal.START, GroupAndSignal.objects.get(group_id=2).signal)
        self.assertEqual(GroupAndSignal.START, GroupAndSignal.objects.get(group_id=3).signal)

    def test_finish(self):
        bot = BotCore()
        message = bot.finish_signal(2)
        bot.finish_signal(1)
        bot.finish_signal(3)
        self.assertEqual(message, "Calculation has already been finished. "
                                  "Before starting the calculations we can not finish calculations. "
                                  "Please start first.")
        self.assertEqual(GroupAndSignal.FINISH, GroupAndSignal.objects.get(group_id=1).signal)
        self.assertEqual(False, GroupAndSignal.objects.filter(group_id=3).exists())


class CalculationTestCase(TestCase):
    def setUp(self) -> None:
        self.expense_group = ExpenseGroup.objects.create(count=3, group_id=1)
        self.expense_group_next = ExpenseGroup.objects.create(count=2, group_id=1)
        user1 = User.objects.create(username='A', group_id=1)
        user2 = User.objects.create(username='B', group_id=1)
        user3 = User.objects.create(username='C', group_id=1)
        group = GroupAndSignal.objects.create(group_id=1, signal=GroupAndSignal.START)
        Expense.objects.create(user=user1, group=group, expense_amount=2000, expense_group=self.expense_group)
        Expense.objects.create(user=user2, group=group, expense_amount=1000, expense_group=self.expense_group)
        Expense.objects.create(user=user3, group=group, expense_amount=300, expense_group=self.expense_group)
        Expense.objects.create(user=user1, group=group, expense_amount=2000, expense_group=self.expense_group_next)
        Expense.objects.create(user=user2, group=group, expense_amount=1000, expense_group=self.expense_group_next)

    def tearDown(self) -> None:
        ExpenseGroup.objects.all().delete()
        User.objects.all().delete()
        GroupAndSignal.objects.all().delete()
        Expense.objects.all().delete()
        Calculation.objects.all().delete()

    def test_calculate(self):
        bot = BotCore()
        bot.calculate(self.expense_group.id)
        self.assertEqual(3, Calculation.objects.count())
        self.assertEqual(0, Calculation.objects.aggregate(total=Sum('debt')).get('total'))
        bot.calculate(self.expense_group_next.id)
        self.assertEqual(5, Calculation.objects.count())
        self.assertEqual(0, Calculation.objects.aggregate(total=Sum('debt')).get('total'))

    def test_get_end_calculations(self):
        bot = BotCore()
        bot.calculate(self.expense_group.id)
        bot.calculate(self.expense_group_next.id)
        debt_A = -1400
        debt_B = 600
        debt_C = 800
        test_messages_list = [f"{user}'s total debt is -> {'<b>{:,.3f}</b>'.format(debt)}\n" for user, debt in
                              [('A', debt_A), ('B', debt_B), ('C', debt_C)]]
        test_message = "".join(test_messages_list)
        message, start_date, end_date = bot.get_end_calculations(1)
        self.assertEqual(message, test_message)

    def test_end_calculations(self):
        bot = BotCore()
        bot.calculate(self.expense_group.id)
        bot.calculate(self.expense_group_next.id)
        bot.end_calculations(1)
        self.assertEqual(0, GroupAndSignal.objects.filter(group_id=1).count())
        self.assertEqual(0, ExpenseGroup.objects.filter(group_id=1).count())
        self.assertEqual(0, Calculation.objects.filter(group_id=1).count())
        self.assertEqual(0, Expense.objects.filter(group_id=1).count())
