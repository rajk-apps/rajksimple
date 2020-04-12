from django.db import models
from django.forms import ModelForm


class Account(models.Model):

    id = models.CharField(max_length=15, primary_key=True)
    name = models.TextField()
    description = models.TextField()
    secret_key = models.CharField(max_length=100)
    merchid = models.CharField(max_length=100)
    order_num = models.IntegerField(default=1)
    is_live = models.BooleanField(default=False)

    default_cause = models.ForeignKey(
        "Cause",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="default_cause",
    )

    submittext = models.CharField(max_length=40, default="Bankkártyás Fizetés")

    def __str__(self):
        return self.name


class Cause(models.Model):

    id = models.CharField(max_length=15, primary_key=True)
    name = models.TextField()
    description = models.TextField()
    default_price = models.PositiveIntegerField(null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Transaction(models.Model):

    id = models.CharField(max_length=100, primary_key=True)

    cause = models.ForeignKey(Cause, on_delete=models.DO_NOTHING)
    amount = models.PositiveIntegerField()
    email = models.EmailField()

    REPS = MARKUP_CHOICES = [
        (0, "Egyszeri"),
        # (1, "Havonta"),
        # (3, "Negyedévente"),
        # (6, "Félévente"),
        # (12, "Évente"),
    ]

    repetition = models.IntegerField(choices=REPS, default=0)
    token = models.CharField(max_length=200, null=True, blank=True)

    STATUSES = [(k, k) for k in ["pending", "confirmed", "denied"]]

    status = models.CharField(
        max_length=10, choices=STATUSES, default="pending"
    )

    confirm_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.cause} - {self.amount} - {self.email} - {self.status} - {self.confirm_date}"


class TransactionForm(ModelForm):
    def __init__(self, *args, **kwargs):

        acc_id = kwargs.pop("account_id")
        super().__init__(*args, **kwargs)

        self.fields["cause"].queryset = Cause.objects.filter(account=acc_id)

        account_inst = Account.objects.get(id=acc_id)
        basecause = account_inst.default_cause

        if basecause is None and (len(self.fields["cause"].queryset) > 0):
            basecause = self.fields["cause"].queryset[0]

        if basecause is not None:
            self.fields["amount"].initial = basecause.default_price
            self.fields["cause"].initial = basecause.id

    class Meta:
        model = Transaction
        fields = [
            "email", 
            # "repetition", 
            "cause", 
            "amount"
        ]

        labels = {
            "email": ("email cím"),
            "amount": ("összeg"),
            "cause": ("tárgy"),
            # "repetition": ("gyakoriság"),
        }
