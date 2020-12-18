grecaptcha.ready(function() {
    grecaptcha.execute('6LfysfwZAAAAAGMM2xnFWQlcL5HAFKJ4oKM0fIzF', {action: 'form'})
    .then(function(token) {
        let input = document.createElement("input");
        input.setAttribute("type", "hidden");
        input.setAttribute("name", "g-recaptcha-response");
        input.setAttribute("value", `${token}`);
        document.getElementById("form").appendChild(input);
    });
});

// document.getElementById("btn").addEventListener('click', doSomething);