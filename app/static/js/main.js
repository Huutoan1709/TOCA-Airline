const dropdowns = document.querySelectorAll('.dropdown')
dropdowns.forEach((d) => {
    d.addEventListener('click', (e) => {
        e.stopPropagation()
        e.target.classList.toggle('open')

        console.log('sdg')
    })

    let items = d.children[1].children


    for (let i = 0; i < items.length; i++) {
        items[i].addEventListener('click', () => {
            d.querySelector('.dropdown-value').value = items[i].dataset['code']
            d.classList.remove('open')
        })
    }
})

window.addEventListener('click', (e) => {
    if (e.target.matches('.dropdown') === false) {
        dropdowns.forEach((d) => {
            d.classList.remove('open')
        })
    }
})


function showDetail(flight, ticketClass) {
    var currentURL = window.location.href;

    var updatedURL = window.location.href;

    if (currentURL.includes('flight=')) {
        updatedURL = currentURL.replace(/(\?|&)flight=[^&]*/, '$1flight=' + flight);
    } else {
        updatedURL = currentURL + (currentURL.includes('?') ? '&' : '?') + 'flight=' + flight;
    }

    if (currentURL.includes('ticket-class=')) {
        updatedURL = updatedURL.replace(/(\?|&)ticket-class=[^&]*/, '$1ticket-class=' + ticketClass);
    } else {
        updatedURL = updatedURL + (currentURL.includes('?') ? '&' : '?') + 'ticket-class=' + ticketClass;
    }

    window.location.href = updatedURL
}


const login = document.querySelector('.login-form')
const register = document.querySelector('.register-form')

function switchForm() {
    login.classList.toggle('hide')
    register.classList.toggle('hide')
}

loginModal = document.getElementById('modal-login')

function openLoginModal() {
    loginModal.classList.add('open')
}

function closeLoginModal() {
    loginModal.classList.remove('open')
}

function showOrderForm() {
    orderForm = document.getElementById('frmCreateOrder')
    orderForm.classList.remove('hide')
}

function showMessage(type) {
    var message = document.getElementById(type + 'Message');
    message.style.animation = 'slideIn 0.3s ease';
    message.style.right = '10px';
    message.style.opacity = '1';

    // Ẩn sau 3 giây
    setTimeout(function () {
        message.style.animation = 'slideOut 0.3s ease';
        message.style.right = '-200px';
        message.style.opacity = '0';
    }, 3000);
}

window.onload = function () {
    // Hiển thị các loại thông báo
    showMessage('info');
    setTimeout(function () {
        showMessage('success');
    }, 3500);
    setTimeout(function () {
        showMessage('fail');
    }, 7000);

}

