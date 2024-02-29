from flask import request, redirect
from app import settings
from app.vnpay import vnpay
from datetime import datetime


def get_prev_url():
    referer = request.headers.get('Referer')

    if referer and referer != request.url:
        return referer
    else:
        return '/'


def check_date(from_date, to_date):
    time_format = "%Y-%m-%dT%H:%M"
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, time_format)
    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, time_format)
    return (to_date - from_date).total_seconds() / 3600


def check_same_date(from_date, to_date):
    return from_date.day == to_date.day and from_date.month == to_date.month and from_date.year == to_date.year


def format_date(date):
    return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")


def pay(order_id):
    order_type = request.form['order_type']
    amount = int(request.form['amount'])
    order_desc = request.form['order_desc']
    bank_code = request.form['bank_code']
    language = request.form['language']
    ipaddr = request.remote_addr
    # Build URL Payment

    vnp = vnpay()
    vnp.requestData['vnp_Version'] = '2.1.0'
    vnp.requestData['vnp_Command'] = 'pay'
    vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
    vnp.requestData['vnp_Amount'] = amount * 100
    vnp.requestData['vnp_CurrCode'] = 'VND'
    vnp.requestData['vnp_TxnRef'] = order_id
    vnp.requestData['vnp_OrderInfo'] = order_desc
    vnp.requestData['vnp_OrderType'] = order_type
    # Check language, default: vn
    if language and language != '':
        vnp.requestData['vnp_Locale'] = language
    else:
        vnp.requestData['vnp_Locale'] = 'vn'
        # Check bank_code, if bank_code is empty, customer will be selected bank on VNPAY
    if bank_code and bank_code != "":
        vnp.requestData['vnp_BankCode'] = bank_code

    vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp.requestData['vnp_IpAddr'] = ipaddr
    vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL
    vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
    print(vnpay_payment_url)
    # Redirect to VNPAY
    return redirect(vnpay_payment_url)
