import datetime
import hmac
import random

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .constants import HOST_ADDRESS
from .models import Account, Cause, Transaction, TransactionForm


def accountview(request, account_id):
    if account_id is None:
        account_inst = None
        causes = []
        form = None
    else:
        account_inst = get_object_or_404(Account, id=account_id)
        causes = account_inst.cause_set.all()
        form = TransactionForm(account_id=account_id)
    accounts = Account.objects.get_queryset()

    return render(
        request,
        "rajksimple/account.html",
        {
            "causes": causes,
            "accounts": accounts,
            "accinst": account_inst,
            "form": form,
        },
    )


def home(request):
    accounts = Account.objects.order_by("order_num")
    first_acc = accounts.first()
    if first_acc is not None:
        acc_id = first_acc.id
    else:
        acc_id = None
    return accountview(request, acc_id)


def backref(request, orderid):

    acdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    acc = Transaction.objects.get(id=orderid).cause.account

    rc = request.GET.get("RC", "cancelled")

    succ = (rc[:3] == "000") or (rc[:3] == "001")

    cut_url = f"{HOST_ADDRESS}{request.get_full_path()}"[:-38]

    validate_hash_base = f"{len(bytes(cut_url, 'utf-8'))}{cut_url}"

    validate_digest = hmac.new(acc.secret_key.encode("utf-8"))
    validate_digest.update(validate_hash_base.encode("utf-8"))
    validate_hash = validate_digest.hexdigest()

    if validate_hash != request.GET.get("ctrl", ""):
        succ = False

    return render(
        request,
        "rajksimple/backref.html",
        {
            "orderid": orderid,
            "payrefno": request.GET.get("payrefno", ""),
            "succ": succ,
            "cancelled": (rc == "cancelled"),
            "date": acdate,
        },
    )


@csrf_exempt
def ipn(request):

    transaction = Transaction.objects.get(id=request.POST.get("REFNOEXT", ""))
    acc = transaction.cause.account

    validate_hash_base = ""

    for k, v in request.POST.items():
        if k != "HASH":
            validate_hash_base += str(len(bytes(v, "utf-8")))
            validate_hash_base += str(v)

    validate_digest = hmac.new(acc.secret_key.encode("utf-8"))
    validate_digest.update(validate_hash_base.encode("utf-8"))
    validate_hash = validate_digest.hexdigest()

    if validate_hash != request.POST["HASH"]:
        transaction.status = "denied"
        transaction.confirm_date = datetime.datetime.now()
        transaction.save()
        return HttpResponse(validate_hash)

    transaction.status = "confirmed"
    transaction.token = request.POST.get("TOKEN")
    transaction.confirm_date = datetime.datetime.now()
    transaction.save()

    keylist = ["IPN_PID[]", "IPN_PNAME[]", "IPN_DATE", "DATE"]

    postreq = {}

    for k in keylist[:-1]:
        postreq[k] = request.POST.get(k, "")

    postreq["DATE"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    source_string = ""

    for k in keylist:
        source_string += str(len(bytes(postreq[k], "utf-8")))
        source_string += postreq[k]

    digest = hmac.new(acc.secret_key.encode("utf-8"))
    digest.update(source_string.encode("utf-8"))
    hash = digest.hexdigest()
    return HttpResponse(f"<EPAYMENT>{postreq['DATE']}|{hash}</EPAYMENT>")


def confirm(request):

    acc = Account.objects.get(id=request.POST.get("account", ""))

    cause = Cause.objects.get(id=request.POST.get("cause", ""))

    orderid = str(datetime.datetime.now().timestamp()).replace(".", "") + str(
        random.randint(1000, 9999)
    )

    form = TransactionForm(request.POST, account_id=acc.id)
    newtrans = form.save(commit=False)
    newtrans.id = orderid
    newtrans.save()

    postreq = {
        "MERCHANT": acc.merchid,
        "ORDER_REF": orderid,
        "ORDER_DATE": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ORDER_PNAME[]": cause.name,
        "ORDER_PCODE[]": cause.id,
        "ORDER_QTY[]": "1",
        "ORDER_VAT[]": "0",
        "PRICES_CURRENCY": "HUF",
    }

    postreq["BILL_EMAIL"] = request.POST.get("email", "")
    postreq["ORDER_PRICE[]"] = request.POST.get("amount", "")
    postreq["BILL_COMPANY"] = request.POST.get("classOf", "")
    postreq["BILL_FNAME"] = request.POST.get("firstName", "")
    postreq["BILL_LNAME"] = request.POST.get("lastName", "")
    postreq["BILL_ADDRESS2"] = request.POST.get("comment", "")

    token = request.POST.get("repetition", "")
    if token != "0":
        postreq["LU_ENABLE_TOKEN"] = True

    keylist = [
        "MERCHANT",
        "ORDER_REF",
        "ORDER_DATE",
        "ORDER_PNAME[]",
        "ORDER_PCODE[]",
        "ORDER_PRICE[]",
        "ORDER_QTY[]",
        "ORDER_VAT[]",
        "PRICES_CURRENCY",
    ]

    source_string = ""

    for k in keylist:
        source_string += str(len(bytes(postreq[k], "utf-8")))
        source_string += postreq[k]

    digest = hmac.new(bytes(acc.secret_key, "utf-8"))
    digest.update(source_string.encode("utf-8"))
    hash = digest.hexdigest()

    postreq["ORDER_HASH"] = str(hash)

    disp = [
        postreq["BILL_EMAIL"],
        str(postreq["ORDER_PRICE[]"]) + " Ft",
        # [x for x in Transaction.REPS if x[0] == int(token)][0][1],
        postreq["BILL_LNAME"],
        postreq["BILL_FNAME"],
        postreq["ORDER_PNAME[]"],
    ]

    return render(
        request,
        "rajksimple/confirm.html",
        {
            "req": postreq,
            "disp": disp,
            "orderid": orderid,
            "host_address": HOST_ADDRESS,
            "is_live": acc.is_live,
        },
    )
