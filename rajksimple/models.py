from django.db import models
from django.forms import ModelForm


class Config(models.Model):

    default_acc = models.ForeignKey(
        "Account", null=True, blank=True, on_delete=models.DO_NOTHING
    )


class Account(models.Model):

    id = models.CharField(max_length=15, primary_key=True)
    name = models.TextField()
    description = models.TextField()
    secret_key = models.CharField(max_length=100)
    merchid = models.CharField(max_length=100)

    default_cause = models.ForeignKey(
        "Cause",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="default_cause",
    )

    submittext = models.CharField(max_length=40, null=True, blank=True)


class Cause(models.Model):

    id = models.CharField(max_length=15, primary_key=True)
    name = models.TextField()
    description = models.TextField()

    starter_price = models.PositiveIntegerField(blank=True, null=True)

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
        (1, "Havonta"),
        (3, "Negyedévente"),
        (6, "Félévente"),
        (12, "Évente"),
    ]

    repetition = models.IntegerField(choices=REPS, default=0)

    token = models.CharField(max_length=200, null=True, blank=True)

    def __str(self):
        return self.name


class TransactionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        acc_id = kwargs.pop("account")
        super(TransactionForm, self).__init__(*args, **kwargs)

        self.fields["cause"].queryset = Cause.objects.filter(account=acc_id)

        try:
            basecause = Account.objects.get(id=acc_id).default_cause
            self.fields["amount"].initial = basecause.starter_price
            self.fields["cause"].initial = basecause.id
        except:
            basecause = self.fields["cause"].queryset[0]
            self.fields["amount"].initial = basecause.starter_price
            self.fields["cause"].initial = basecause.id

    class Meta:
        model = Transaction
        fields = ["email", "repetition", "cause", "amount"]

        labels = {
            "email": ("email cím"),
            "amount": ("összeg"),
            "cause": ("tárgy"),
            "repetition": ("gyakoriság"),
        }
