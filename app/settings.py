import enum

VNPAY_TMN_CODE = 'WNWB9V0T'
VNPAY_RETURN_URL = 'http://127.0.0.1:5000/payment-result'
VNPAY_HASH_SECRET_KEY = 'IOIDHPEXPTMAHCKDBICMSKKWBSKCLGFN'
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'


class Regulation(enum.Enum):
    FLIGHT_TIME_MAX = 1
    TERMINATION_NUM_MAX = 2
    STOP_MIN = 3
    STOP_MAX = 4
    TICKET_CLASS = 5
    TICKET1_PRICES = 6
    TICKET2_PRICES = 7
    SALE_TIME = 8
    ORDER_TIME = 9
    AIRPORT_MAX = 10
