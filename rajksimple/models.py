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

    # Évfolyam
    classOf = models.CharField(max_length=128, null=True, blank=True)

    # Név
    firstName = models.CharField(max_length=64, null=True, blank=True)
    lastName = models.CharField(max_length=64, null=True, blank=True)

    # Megjegyzés
    comment = models.CharField(max_length=128, null=True, blank=True)

    token = models.CharField(max_length=200, null=True, blank=True)

    STATUSES = [(k, k) for k in ["pending", "confirmed", "denied"]]

    status = models.CharField(
        max_length=10, choices=STATUSES, default="pending"
    )

    confirm_date = models.DateTimeField(blank=True, null=True)
    repetition = models.SmallIntegerField(blank=True, default=0)
    is_live = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return " - ".join(
            map(
                str,
                [
                    self.cause,
                    self.amount,
                    self.email,
                    self.classOf,
                    self.status,
                    self.confirm_date,
                    self.firstName,
                    self.lastName,
                    self.comment,
                ],
            )
        )


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
            "classOf",
            "firstName",
            "lastName",
            "comment",
            # "repetition",
            "cause",
            "amount",
        ]

        labels = {
            "email": ("email cím"),
            "amount": ("összeg"),
            "cause": ("tárgy"),
            "classOf": ("évfolyam"),
            "firstName": ("keresztnév"),
            "lastName": ("családnév"),
            "comment": ("megjegyzés")
            # "repetition": ("gyakoriság"),
        }
