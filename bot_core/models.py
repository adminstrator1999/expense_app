from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


class QuerySet(models.QuerySet):
    def delete(self):
        self.update(is_deleted=True)


class BaseManager(models.Manager):
    def get_queryset(self):
        return QuerySet(self.model).filter(is_deleted=False)


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)

    objects = BaseManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class Group(BaseModel):
    group_id = models.CharField(max_length=255, unique=True)
    members_count = models.IntegerField()


class GroupAndSignal(models.Model):
    START = 'start'
    FINISH = 'finish'
    SIGNALS = (
        (START, START),
        (FINISH, FINISH)
    )
    signal = models.CharField(max_length=6, choices=SIGNALS)
    group_id = models.CharField(max_length=255)


class User(AbstractBaseUser, DeleteMixin):
    username = models.CharField(max_length=123)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    group_id = models.CharField(max_length=255)
    USERNAME_FIELD = 'username'


class ExpenseGroup(BaseModel):
    group_id = models.CharField(max_length=255)
    count = models.IntegerField()


class Expense(BaseModel, DeleteMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    expense_amount = models.FloatField(default=None)
    group = models.ForeignKey(GroupAndSignal, on_delete=models.CASCADE, default=None)
    expense_group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, default=None)


class Calculation(BaseModel, DeleteMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    debt = models.FloatField()
    group = models.ForeignKey(GroupAndSignal, on_delete=models.CASCADE)


class MessageLog(BaseModel):
    group_id = models.CharField(max_length=255)
    message = models.TextField()
