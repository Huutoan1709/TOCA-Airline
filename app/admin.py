from datetime import datetime
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from app.models import SanBay, TuyenBay, MayBay, ChuyenBay, Ve, HangVe, Ghe, DungChan, NguoiDung, HoaDon, UserRole, \
    QuyDinh
from app import db, app, dao, utils
from flask_login import current_user, logout_user
from flask import redirect, request, flash
from app.settings import Regulation

admin = Admin(app=app, template_mode='bootstrap4', name='TOCA Admin')


class EmployeeBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.EMPLOYEE


class AdminBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class SaleView(EmployeeBaseView):
    @expose('/', methods=['post', 'get'])
    def index(self):
        try:
            global flights
            flights = None
            from_loc = request.args.get('from-location')
            to_loc = request.args.get('to-location')

            flight_date = request.args.get('flight-date')
            flight_date = flight_date if flight_date != '' else None
            if flight_date and datetime.strptime(flight_date, "%Y-%m-%d") <= datetime.now():
                raise Exception('Ngày đi phải sau ngày hiện tại!!!')

            if from_loc and to_loc:
                from_code = dao.get_airport_id(from_loc)
                to_code = dao.get_airport_id(to_loc)
                flights = dao.search_flight(from_code, to_code, flight_date)

            flight = dao.get_flight_by_id(request.args.get('flight'))
            ticket_class = dao.get_ticket_class_by_id(request.args.get('ticket-class'))
            if flight and utils.check_date(datetime.now(), flight.gio_bay) <= dao.get_regulation_value(
                    Regulation.SALE_TIME.value):
                raise Exception('Ngoài thời gian bán vé cho phép')
            global user
            global bill
            user = bill = None
            if request.method == 'POST':
                fname = request.form.get('fname')
                lname = request.form.get('lname')
                # is_adult = request.form.get('adult')
                gender = request.form.get('gender')
                dob = request.form.get('dob')
                nationality = request.form.get('nationality')
                phone = request.form.get('phone')
                email = request.form.get('email')
                address = request.form.get('address')

                c = {}
                c['name'] = lname + " " + fname
                # c['is_adult'] = is_adult.__eq__('true')
                c['gender'] = gender
                c['dob'] = dob
                c['nationality'] = nationality
                c['phone'] = phone
                c['email'] = email
                c['address'] = address

                user = dao.create_customer(name=c['name'], gender=c['gender'], dob=c['dob'],
                                           nationality=c['nationality'], phone=c['phone'],
                                           email=c['email'], address=c['address'])

                bill = dao.create_bill(current_user.id, (flight.gia + ticket_class.gia) * 1.08)
                dao.create_ticket(flight_id=flight.id, ticket_class_id=ticket_class.id, customer_id=user.id,
                                  bill_id=bill.id)

            return self.render('/admin/sale-ticket.html', flights=flights, flight=flight,
                               ticket_class=ticket_class, user=user, bill=bill)
        except Exception as e:
            flash(str(e.args[0]), 'error')
            print(e)
            return redirect(utils.get_prev_url())


class StatsView(AdminBaseView):
    @expose('/', methods=['post', 'get'])
    def stats(self):
        global stats, from_date, to_date
        stats = dao.get_stats()
        from_date = to_date = None

        if request.method == 'POST':
            from_date = request.form.get('from-date')
            to_date = request.form.get('to-date')

            if not to_date:
                to_date = utils.format_date(datetime.now())

            stats = dao.get_stats(from_date, to_date)

        total_turn = 0
        total_sale = 0
        for s in stats:
            total_turn += s[2]
            total_sale += s[3]
        return self.render('/admin/stats.html', stats=stats, total_turn=total_turn,
                           total_sale=total_sale, empty=stats == [],
                           from_date=from_date, to_date=to_date)


class ScheduleView(EmployeeBaseView):
    @expose('/', methods=['post', 'get'])
    def index(self):
        try:
            scheduled_flights = dao.get_scheduled_fllights()
            flight_id = request.args.get('flight-id')
            flight = dao.get_flight_by_id(flight_id)
            seats = dao.get_seats(flight_id)
            terms = dao.get_terms(flight_id)

            max_term = dao.get_regulation_value(Regulation.TERMINATION_NUM_MAX.value)

            if request.method == 'POST':
                form = request.form
                if flight:
                    flight.gio_bay = form.get('flight-from-date')
                    flight.gio_den = form.get('flight-to-date')

                    if utils.check_date(flight.gio_bay, flight.gio_den) > dao.get_regulation_value(
                            Regulation.FLIGHT_TIME_MAX.value) / 60:
                        raise Exception(
                            f'Thời gian bay tối đa là {dao.get_regulation_value(Regulation.FLIGHT_TIME_MAX.value)} phút !!')

                    flight.gia = form.get('flight-price')
                    flight_seats = form.getlist('flight-seat-num')
                    flight_terms = form.getlist('term-id')

                    for i, c in enumerate(dao.get_ticket_classes()):
                        if int(flight_seats[i]) <= 0:
                            raise Exception('Chưa hoàn thành số lượng các hạng ghế!!!')
                        dao.set_seat(flight_id, c.id, flight_seats[i])

                    for i in range(len(flight_terms)):
                        if flight_terms[i] != '0':
                            time = int(form.getlist('term-time')[i]) if form.getlist('term-time') else 30
                            time_max = dao.get_regulation_value(Regulation.STOP_MAX.value)
                            time_min = dao.get_regulation_value(Regulation.STOP_MIN.value)
                            if time > time_max or time < time_min:
                                raise Exception(f'Thời gian dừng tối thiểu {time_min} phút và tối đa {time_max} phút')

                            note = form.getlist('term-note')[i] if form.getlist('term-note') else ''
                            dao.set_terms(flight_id, flight_terms[i], time, note)

                return redirect('/admin/scheduleview')

            if request.args.get('done'):

                flight.san_sang = True
                db.session.add(flight)
                db.session.commit()
                return redirect('/admin/scheduleview')

            return self.render('/admin/schedule.html', scheduled_flights=scheduled_flights, flight=flight, seats=seats,
                               terms=terms, max_term=max_term)
        except Exception as e:
            flash(str(e.args[0]), 'error')
            print(e)
            return redirect('/admin/scheduleview')


class ChangeRegulationView(AdminBaseView):
    @expose('/')
    def index(self):
        return self.render('/admin/change-regulation.html')


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


class EmployeeView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.EMPLOYEE


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class MySanBayView(AdminView):
    create_modal = True
    column_list = ['name', 'diaChi']
    column_labels = {
        'diaChi': 'Địa chỉ'
    }


class MyTuyenBayView(AdminView):
    create_modal = True
    column_list = ['name', 'sanbaydi.name', 'sanbayden.name', 'chuyenbays']
    column_labels = {
        'sanbaydi.name': 'Sân bay khởi hành',
        'sanbayden.name': 'Sân bay đến',
        'chuyenbays': 'Danh sách chuyến bay',
        'name': 'Tuyến'
    }
    column_searchable_list = ['name', 'sanbaydi.name', 'sanbayden.name']
    form_excluded_columns = ['chuyenbays']


class MyChuyenBayView(AdminView):
    create_modal = True
    column_list = ['name', 'maybay', 'gia', 'gio_bay', 'gio_den', 'tuyenbay']
    form_excluded_columns = ['ghes', 'ves', 'tramdungs', 'san_sang']


class MyMayBayView(AdminView):
    column_list = ['name']


class MyHangveView(AdminView):
    column_labels = {
        'quyenloi': 'Quyền lợi',
        'gia': 'Giá',
        'name': 'Tên'
    }


class MyVeView(EmployeeView):
    can_create = False
    column_list = ['tong_tien_ve', 'hanhkhach.name', 'chuyenbay.tuyenbay', 'hangve', 'hoadon.da_thanh_toan']
    column_filters = ['chuyenbay.tuyenbay', 'hangve']
    column_searchable_list = ['hanhkhach.name']
    column_labels = {
        'tong_tien_ve': 'Tổng tiền vé',
        'hanhkhach.name': 'Tên hành khách',
        'chuyenbay.tuyenbay': 'Tuyến bay',
        'hangve': 'Hạng vé',
        'hoadon.da_thanh_toan': 'Thanh toán'

    }


class RegulationView(AdminView):
    column_editable_list = ['gia_tri']
    edit_modal = True


admin.add_view(SaleView(name='Bán vé'))
admin.add_view(ScheduleView(name='Lập lịch chuyến bay'))
admin.add_view(MyVeView(Ve, db.session, name='Vé'))

admin.add_view(StatsView(name='Báo cáo thống kê'))
admin.add_view(RegulationView(QuyDinh, db.session, name='Thay đổi quy định'))
admin.add_view(MySanBayView(SanBay, db.session, name='Sân Bay'))
admin.add_view(MyMayBayView(MayBay, db.session, name='Máy Bay'))
admin.add_view(MyHangveView(HangVe, db.session, name='Hạng Vé'))
admin.add_view(MyTuyenBayView(TuyenBay, db.session, name='Tuyến Bay'))
admin.add_view(MyChuyenBayView(ChuyenBay, db.session, name='Chuyến Bay'))
admin.add_view(AdminView(NguoiDung, db.session, name='Người dùng'))
admin.add_view(LogoutView(name='Đăng xuất'))
