import hashlib

from sqlalchemy import func
from flask import session
from app import db, utils
from app.models import SanBay, TuyenBay, ChuyenBay, HangVe, NguoiDung, HanhKhach, Ve, HoaDon, QuyDinh, Ghe, DungChan
from cloudinary import uploader


def load_regulation():
    regulations = {
        'Thời gian bay tối thiểu (phút)': 30,
        'Số sân bay trung gian tối đa': 2,
        'Thời gian dừng tối thiểu(phút)': 20,
        'Thời gian dừng tối đa(phút)': 30,
        'Số lượng hạng vé': 2,
        'Giá vé hạng 1': 800,
        'Giá vé hạng 2': 500,
        'Thời gian bán vé trước (giờ)': 4,
        'Thời gian đặt vé trước (giờ)': 12,
        'Số sân bay tối đa': 10
    }

    for (label, value) in regulations.items():
        r = QuyDinh(noi_dung=label, gia_tri=value)
        db.session.add(r)

    db.session.commit()


def get_regulations():
    regulation = QuyDinh.query.all()
    regulation_dict = {}
    for r in regulation:
        regulation_dict[r.noi_dung] = r.gia_tri
    return regulation_dict


def get_regulation_value(id):
    reg = QuyDinh.query.filter(QuyDinh.id.__eq__(id)).first()

    if reg:
        return reg.gia_tri


def set_regulation(id, new_value):
    regulation = QuyDinh.query.get(id)
    regulation.gia_tri = new_value
    db.session.add(regulation)
    db.session.commit()


def get_stats(from_date=None, to_date=None):
    if from_date and to_date:
        result = db.session.query(TuyenBay.id, TuyenBay.name, func.count(ChuyenBay.id), func.sum(Ve.tong_tien_ve)) \
            .join(ChuyenBay, TuyenBay.id == ChuyenBay.tuyenbay_id, isouter=True) \
            .filter(ChuyenBay.gio_bay.between(from_date, to_date)) \
            .join(Ve, ChuyenBay.id == Ve.chuyenbay_id) \
            .join(HoaDon, Ve.hoadon_id == HoaDon.id) \
            .filter(HoaDon.da_thanh_toan == True) \
            .group_by(TuyenBay.id) \
            .all()
    else:
        result = db.session.query(TuyenBay.id, TuyenBay.name, func.count(ChuyenBay.id), func.sum(Ve.tong_tien_ve)) \
            .join(ChuyenBay, TuyenBay.id == ChuyenBay.tuyenbay_id, isouter=True) \
            .join(Ve, ChuyenBay.id == Ve.chuyenbay_id) \
            .join(HoaDon, Ve.hoadon_id == HoaDon.id) \
            .filter(HoaDon.da_thanh_toan == True) \
            .group_by(TuyenBay.id) \
            .all()

    return result


def get_airports():
    return SanBay.query.all()


def get_scheduled_fllights():
    scheduled_fllights = ChuyenBay.query.filter(ChuyenBay.san_sang.__eq__(False))
    return scheduled_fllights.all()


def get_airport_by_id(id):
    return SanBay.query.get(id)


def get_airport_id(airport_name):
    airport = SanBay.query.filter(SanBay.name.__eq__(airport_name)).first()
    return airport.id


def get_airport_name(id):
    return SanBay.query.get(id).name


def get_ticket_class_by_id(id=None):
    return HangVe.query.get(id)


def get_tickets_for_customer(user_id):
    return db.session.query(Ve) \
        .join(HoaDon, Ve.hoadon_id == HoaDon.id) \
        .filter(HoaDon.nguoi_thanh_toan_id == user_id) \
        .order_by(Ve.id.desc()) \
        .all()


def get_bill_by_id(bill_id):
    return HoaDon.query.get(bill_id)


def get_ticket_classes():
    return HangVe.query.all()


def get_flight_by_id(id=None):
    return ChuyenBay.query.get(id)


def get_flights(ready=False):
    return ChuyenBay.query.filter(ChuyenBay.san_sang.__eq__(ready)).all()


def get_routes():
    return TuyenBay.query.all()


def search_flight(from_code, to_code, date=None, ready=False):
    t = TuyenBay.query.filter(TuyenBay.sanBayKhoiHanh_id.__eq__(from_code),
                              TuyenBay.sanBayDen_id.__eq__(to_code))
    if t.first():
        if date:
            ds_chuyenbay = ChuyenBay.query.filter(ChuyenBay.san_sang == True,
                                                  ChuyenBay.tuyenbay_id.__eq__(t.first().id),
                                                  func.DATE(ChuyenBay.gio_bay) == date)
            return ds_chuyenbay.all()
        else:
            ds_chuyenbay = ChuyenBay.query.filter(ChuyenBay.san_sang == True,
                                                  ChuyenBay.tuyenbay_id.__eq__(t.first().id))
            return ds_chuyenbay.all()
    else:
        return []


def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)


def create_customer(name, phone, email, nationality, **kwargs):
    c = HanhKhach(name=name,
                  email=email,
                  phone=phone,
                  # ngay_sinh=dob,
                  gioi_tinh=kwargs.get('gender'),
                  # la_nguoi_lon=kwargs.get('is_adult'),
                  quoc_tich=nationality,
                  dia_chi=kwargs.get('address')
                  )
    db.session.add(c)
    db.session.commit()
    return c


def create_bill(nguoi_thanh_toan_id, tong_hoa_don=0):
    b = HoaDon(nguoi_thanh_toan_id=nguoi_thanh_toan_id, tong_hoa_don=tong_hoa_don)
    db.session.add(b)
    db.session.commit()
    return b


def create_ticket(flight_id, ticket_class_id, customer_id, bill_id):
    t = Ve(hangve_id=ticket_class_id, chuyenbay_id=flight_id, hanhkhach_id=customer_id, hoadon_id=bill_id)
    flight = get_flight_by_id(flight_id)
    ticket_class = get_ticket_class_by_id(ticket_class_id)
    t.tong_tien_ve = flight.gia + ticket_class.gia

    ghe = Ghe.query.filter(Ghe.chuyenbay_id.__eq__(flight_id),
                           Ghe.hangve_id.__eq__(ticket_class_id)).first()
    ghe.so_luong -= 1
    db.session.add(t)
    db.session.add(ghe)
    db.session.commit()
    return t


def check_exist_user(username):
    user = NguoiDung.query.filter(NguoiDung.username.__eq__(username.strip())).first()
    if user:
        return True
    else:
        return False

def create_user(username, email, password, name, avatar=None):
    u = NguoiDung()
    u.name = name
    u.email = email
    u.username = username
    u.password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    if avatar:
        avatar_result = uploader.upload(avatar)
        u.avatar = avatar_result['secure_url']

    db.session.add(u)
    db.session.commit()


def set_terms(flight_id, airport_id, time=0, note=''):
    term = DungChan.query.filter(DungChan.chuyenbay_id.__eq__(flight_id), DungChan.sanbay_id.__eq__(airport_id)).first()
    if term:
        if time != '':
            term.thoi_gian_dung = time
        term.ghi_chu = note
        db.session.add(term)
        print('co')
    else:
        print('khong')
        term = DungChan()
        term.chuyenbay_id = flight_id
        term.sanbay_id = airport_id
        if time != '':
            term.thoi_gian_dung = time
        term.ghi_chu = note
        db.session.add(term)
    db.session.commit()


def get_seats(flight_id):
    seats = Ghe.query.filter(Ghe.chuyenbay_id.__eq__(flight_id))
    return seats.all()


def get_terms(flight_id):
    terms = DungChan.query.filter(DungChan.chuyenbay_id.__eq__(flight_id))
    return terms.all()


def set_seat(flight_id, class_id, qty):
    seat = Ghe.query.filter(Ghe.chuyenbay_id.__eq__(flight_id), Ghe.hangve_id.__eq__(class_id)).first()
    if seat:
        seat.so_luong = qty
        db.session.add(seat)
    else:
        seat = Ghe()
        seat.chuyenbay_id = flight_id
        seat.hangve_id = class_id
        seat.so_luong = qty
        db.session.add(seat)

    db.session.commit()


def check_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = NguoiDung.query.filter(NguoiDung.username.__eq__(username.strip())).first()

    if u:
        if u.password == password:
            return u
        else:
            raise Exception("Sai mật khẩu!!!")
    else:
        raise Exception("Người dùng không tồn tại")