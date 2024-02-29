from cloudinary import uploader

from app import app, db, dao, utils, login as app_login
from flask import render_template, request, redirect, session, flash
from flask_login import login_user, logout_user, current_user, login_required
from admin import *
from app.settings import Regulation as RegulationEnum


@app.context_processor
def common_response():
    return {
        'airports': dao.get_airports(),
        'routes': dao.get_routes(),
        'ticket_classes': dao.get_ticket_classes(),
        'all_flights': dao.get_flights(ready=True),
        'regulations': dao.get_regulations(),
        'req_enum': RegulationEnum
    }


@app_login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/')
def index():
    return render_template('home.html', home=True)


@app.route('/history')
def history():
    page = request.args.get('page')
    tickets = dao.get_tickets_for_customer(current_user.id)
    return render_template('history.html', tickets=tickets)


@app.route('/select-flight', methods=['get', 'post'])
def select_flight():
    try:
        from_loc = request.args.get('from-location')
        to_loc = request.args.get('to-location')
        if not from_loc:
            raise Exception('Vui lòng chọn địa điểm khởi hành')
        if not to_loc:
            raise Exception('Vui lòng chọn địa điểm đến')

        quantity = request.args.get('quantity')
        flight_date = request.args.get('flight-date')
        flight_date = flight_date if flight_date != '' else None

        if flight_date and datetime.strptime(flight_date, "%Y-%m-%d") <= datetime.now():
            raise Exception('Ngày đi phải sau ngày hiện tại!!!')

        from_code = dao.get_airport_id(from_loc)
        to_code = dao.get_airport_id(to_loc)

        order = session.get('order', {})
        if session.get('customers'):
            del session['customers']

        order['from-code'] = from_code
        order['from'] = from_loc
        order['to-code'] = to_code
        order['to'] = to_loc
        order['quantity'] = quantity
        order['flight_date'] = flight_date

        session['order'] = order
        flights = dao.search_flight(from_code, to_code, flight_date)
        flight = dao.get_flight_by_id(request.args.get('flight'))
        ticket_class = dao.get_ticket_class_by_id(request.args.get('ticket-class'))

        if flights == []:
            raise Exception('Không tồn tại chuyến bay nào phù hợp!!!')

        global terms
        terms = None
        if flight:
            terms = dao.get_terms(flight.id)
        if flight and ticket_class:
            print(utils.check_date(datetime.now(), flight.gio_bay), dao.get_regulation_value(
                RegulationEnum.ORDER_TIME.value))
            if utils.check_date(datetime.now(), flight.gio_bay) <= dao.get_regulation_value(
                    RegulationEnum.ORDER_TIME.value):

                raise Exception('Ngoài thời gian cho phép đặt vé!!')
            session['order']['flight'] = flight.id
            session['order']['ticket-class'] = ticket_class.id

        return render_template('select-flight.html',
                               flight_list=flights, flight=flight, ticket_class=ticket_class, terms=terms)
    except Exception as e:
        flash(str(e.args[0]), 'error')
        print(e)
        return redirect(utils.get_prev_url())


@app.route('/passenger-info', methods=['post', 'get'])
def passenger_info():
    try:
        global cusomer_left

        if session.get('order'):
            cusomer_left = session['order']['quantity']
        else:
            raise Exception('Vui lòng dặt vé !!')

        if request.method == 'POST':
            fname = request.form.get('fname')
            lname = request.form.get('lname')
            is_adult = request.form.get('adult')
            gender = request.form.get('gender')
            dob = request.form.get('dob')
            nationality = request.form.get('nationality')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')

            c = {}
            c['name'] = lname + " " + fname
            c['is_adult'] = is_adult.__eq__('true')
            c['gender'] = gender
            c['dob'] = dob
            c['nationality'] = nationality
            c['phone'] = phone
            c['email'] = email
            c['address'] = address

            customers = session.get('customers', [])

            if c in customers:
                flash('Người dùng đã tồn tại', 'error')
            else:
                customers.append(c)
                session['customers'] = customers

            cusomer_left = int(session['order']['quantity']) - len(session.get('customers', []))

        return render_template('passenger-info.html', cusomer_left=cusomer_left)
    except Exception as e:
        flash(str(e.args[0]), 'error')
        print(e)
        return redirect(utils.get_prev_url())


@app.route('/payment', methods=['post', 'get'])
@login_required
def payment():
    try:
        bill_id = request.args.get('bill_id')
        if request.method == 'POST':
            bill = dao.get_bill_by_id(bill_id)
            return utils.pay(bill.id)
        else:
            customers = session.get('customers')
            flight = dao.get_flight_by_id(session['order']['flight'])
            ticket_class = dao.get_ticket_class_by_id(session['order']['ticket-class'])

            bill = dao.create_bill(current_user.id)
            for c in customers:
                print(c)
                cus = dao.create_customer(name=c['name'], gender=c['gender'],
                                          nationality=c['nationality'], phone=c['phone'], email=c['email'],
                                          address=c['address'])
                ticket = dao.create_ticket(flight_id=flight.id, ticket_class_id=ticket_class.id, customer_id=cus.id,
                                           bill_id=bill.id)
                bill.tong_hoa_don += ticket.tong_tien_ve

            bill.tong_hoa_don *= 1.08
            db.session.add(bill)
            db.session.commit()

        return render_template('payment.html', bill=bill, flight=flight, ticket_class=ticket_class)
    except Exception as e:
        flash(str(e.args[0]), 'error')
        return redirect(utils.get_prev_url())


@app.route('/payment-result')
def payment_result():
    try:
        payment_status = request.args.get('vnp_TransactionStatus') or request.args.get('paid-code')
        status = 'success' if payment_status == '00' else 'fail'
        bill_id = request.args.get('vnp_TxnRef') or request.args.get('bill_id')
        bill = dao.get_bill_by_id(bill_id)
        print(status)
        if status == 'success':
            bill.da_thanh_toan = True
            db.session.add(bill)
            db.session.commit()
            if 'order' in session:
                del session['order']
            if 'customers' in session:
                del session['customers']
        next = request.args.get('next')
        return render_template('payment-result.html', status=status, next=next)

    except Exception as e:
        flash(str(e.args[0]), 'error')
        return redirect(utils.get_prev_url())


@app.route('/register', methods=['post'])
def register():
    try:
        name = request.form.get('name')
        username = request.form.get('username')
        avatar = request.files.get('avatar')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_pw')

        if dao.check_exist_user(username):
            raise Exception("Username đã tồn tại!!!")

        if password == confirm_password:
            dao.create_user(username, email, password, name, avatar)
            return redirect(utils.get_prev_url())
        else:
            flash('Mật khẩu không trùng khớp', 'error')
    except Exception as e:
        flash(str(e.args[0]), 'error')
        return redirect(utils.get_prev_url())
    else:
        flash('Tạo tài khoản thành công', 'success')
        return redirect(utils.get_prev_url())


@app.route('/profile', methods=['post', 'get'])
@login_required
def profile():
    edit = request.args.get('edit') == 'true'
    if request.method == 'POST':
        u = dao.get_user_by_id(current_user.id)
        u.phone = request.form.get('phone')
        u.email = request.form.get('email')
        u.ngay_sinh = request.form.get('dob')
        avatar = request.files.get('avatar')

        if avatar:
            avatar_result = uploader.upload(avatar)
            u.avatar = avatar_result['secure_url']

        db.session.add(u)
        db.session.commit()
    flash('Cập nhật thông tin thành công', 'success')
    return render_template('profile.html', edit=edit)


@app.route('/admin/login', methods=['post'])
def login():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.check_user(username=username, password=password)

        if user:
            login_user(user)
        else:
            flash('Đăng nhập thất bại', 'error')

    except Exception as e:
        flash(str(e.args[0]), 'error')
        return redirect(utils.get_prev_url())
    else:
        return redirect(utils.get_prev_url())


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
