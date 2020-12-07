grecaptcha.ready(function() {
        grecaptcha.execute('6LfysfwZAAAAAGMM2xnFWQlcL5HAFKJ4oKM0fIzF', {action: 'signup_form'})
        .then(function(token) {
            let input = document.createElement("input");
            input.setAttribute("type", "hidden");
            input.setAttribute("name", "g-recaptcha-response");
            input.setAttribute("value", `${token}`);
            document.getElementById("signup_form").appendChild(input);
        });
    });