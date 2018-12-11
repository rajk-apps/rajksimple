from django.shortcuts import render, get_object_or_404
from django.http import Http404
import hmac
import datetime
import random
#from django.contrib.auth.decorators import login_required

from .models import *
from django.http import HttpResponse



def accountview(request,account_id):
    account_inst = get_object_or_404(Account, id=account_id)
    accounts = Account.objects.get_queryset()
    causes = account_inst.cause_set.all()
    form = TransactionForm(account=account_id)
    return render(request, 'rajksimple/account.html', {'causes': causes,
                                                    'accounts':accounts,
                                                    'accinst':account_inst,
                                                    'form':form})


#@login_required
def home(request):
    try:
        mainconf = Config.objects.first()
    except:
        raise Http404("Not yet configured")
    return accountview(request,
                   mainconf.default_acc.id)


def backref(request,orderid):
    
    acdate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    
    RC = request.POST.get('payrefno', "")
    
    succ = (RC[:3] == '000') or (RC[:3] == '001')
    
    return render(request, 'rajksimple/backref.html',
                  {'orderid':orderid,
                  'payrefno':request.GET.get('payrefno', ""),
                  'succ':succ,
                  'date':acdate
                  })

def ipn(request):
    
    acc = Account.objects.get(merchid=request.POST.get("MERCHANT", ""))
    
    keylist = ['IPN_PID[0]','IPN_PNAME[0]','IPN_DATE','DATE']
    
    print(request.POST)
    
    postreq = {}
    
    for k in keylist[:-1]:
        postreq[k] = request.POST.get(k, "")
    
    postreq['DATE'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    
    source_string = ''

    for k in keylist:
        source_string += str(len(bytes(postreq[k],'utf-8')))
        source_string += postreq[k]
    
    
    digest = hmac.new(acc.secret_key)
    digest.update(source_string)
    hash = digest.hexdigest()
    
    return HttpResponse('<EPAYMENT>' + str(hash) + '</EPAYMENT>')



def confirm(request):
    
    
    acc = Account.objects.get(id=request.POST.get("account", ""))
    
    cause = Cause.objects.get(id=request.POST.get("cause", ""))
    
    orderid = str(datetime.datetime.now().timestamp()).replace('.','') + \
                                            str(random.randint(1000,9999))
    
    form = TransactionForm(request.POST)
    newtrans = form.save(commit=False)
    newtrans.id = orderid
    newtrans.save()
    
    postreq ={'MERCHANT':acc.merchid,
        'ORDER_REF':orderid,
        'ORDER_DATE':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'ORDER_PNAME[]':cause.name,
        'ORDER_PCODE[]':cause.id,
        'ORDER_QTY[]':'1',
        'ORDER_VAT[]':'0',
        'PRICES_CURRENCY':'HUF'}

    postreq['BILL_EMAIL'] = request.POST.get("email", "")
    postreq['ORDER_PRICE[]'] = request.POST.get("amount", "")

    token = request.POST.get("repetition", "")
    if token != '0':
        postreq['LU_ENABLE_TOKEN'] = True 



    keylist = ['MERCHANT',
    'ORDER_REF',
    'ORDER_DATE',
    'ORDER_PNAME[]',
    'ORDER_PCODE[]',
    'ORDER_PRICE[]',
    'ORDER_QTY[]',
    'ORDER_VAT[]',
    'PRICES_CURRENCY']
    
    
    source_string = ''

    for k in keylist:
        source_string += str(len(bytes(postreq[k],'utf-8')))
        source_string += postreq[k]
    
    digest = hmac.new(bytes(acc.secret_key,'utf-8'))
    digest.update(source_string.encode('utf-8'))
    hash = digest.hexdigest()
    
    postreq['ORDER_HASH'] = str(hash)
    
    disp = [postreq['BILL_EMAIL'],
            str(postreq['ORDER_PRICE[]']) + ' Ft',
            [x for x in Transaction.REPS if x[0] == int(token)][0][1],
            postreq['ORDER_PNAME[]']]
    
    return render(request, 'rajksimple/confirm.html',{'req':postreq,
                                                      'disp':disp,
                                                      'orderid':orderid})
    
    