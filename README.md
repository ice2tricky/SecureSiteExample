# project structure info
Why Django templates?

Using Django templates protects you against the majority of XSS attacks.

Django templates escape specific characters which are particularly dangerous to HTML.

# security headers implemented
- X-XSS-Protection
- Strict-Transport-Security
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Content-Security-Policy
- Feature-Policy

# URL link
https://enigmatic-tundra-85410.herokuapp.com/

connecting first time can sometimes take a while because the site wakes up on the first connection (free tier)

# site info
superuser: admin - password: student2

full access to everything -> will automatically be redirected to admin panel on login

logged in user will have access to New meeting tab and will be able to login

not logged in can just see planned meetings and the available rooms

#reCAPTCHA info
Added recaptcha security from Google.

Alternative to throttling, that gives a better user experience.

Google AI will scan your form for malicious intent

## site key
6LfysfwZAAAAAGMM2xnFWQlcL5HAFKJ4oKM0fIzF

## site secret
6LfysfwZAAAAAMndxlkywXbWzzYu6LZbiE_Y8jrY