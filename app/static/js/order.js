function addToOrder(id, name, price) {
    fetch('/api/order', {
        method: 'post',
        body: JSON.stringify({
            from,
            to,
            quantity,
            date
        }),
        headers: {
            'Content-Type': 'application/json'
        }

    }).then(function (res) {
        return res.json()
    }).then(function (data) {

    })
}