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

My site received A+ on https://securityheaders.com/

# URL link
https://enigmatic-tundra-85410.herokuapp.com/

connecting first time can sometimes take a while because the site wakes up on the first connection (free tier)

# Dependency update
Keeping a second copy from the code on the link below on github so that dependabot can daily check it and mail me when irregularities are found.

https://github.com/ice2tricky/SecureSiteExample

# Access control policy
admin: admin - password: student2  
Can CRUD users, groups and rooms from the admin panel  
Delete and edit all meetings  
will be automatically be redirected to admin panel on login

logged in user will have access to New meeting tab and add new meetings  
Delete and edit meetings they have made.

not logged in can just see planned meetings and the available rooms

#reCAPTCHA info
Added recaptcha security from Google.

Alternative to throttling, that gives a better user experience.

Google AI will scan your form for malicious intent

## public key
6LfysfwZAAAAAGMM2xnFWQlcL5HAFKJ4oKM0fIzF

## secret key
6LfysfwZAAAAAMndxlkywXbWzzYu6LZbiE_Y8jrY

# Security policy settings

SECURE_BROWSER_XSS_FILTER = True

SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = 'DENY'

SECURE_REFERRER_POLICY = 'same-origin'

SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = CSRF_COOKIE_HTTPONLY = True

CSP_DEFAULT_SRC = [
                   "https://www.google.com/recaptcha/api2/anchor",
                   "'self'"]
                   
CSP_SCRIPT_SRC = [  
    'https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js',  
    "https://code.jquery.com/jquery-3.4.1.slim.min.js",  
    "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js",  
    "https://www.google.com/recaptcha/api.js",  
    "https://enigmatic-tundra-85410.herokuapp.com/static/",  
    "https://www.gstatic.com/recaptcha/releases/",  
    "https://enigmatic-tundra-85410.herokuapp.com/admin/jsi18n/"  
]

CSP_STYLE_SRC = [  
    "'self' https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",  
]

CSP_REPORT_URI = "https://fairplaydesign.report-uri.com/r/d/csp/reportOnly"

PERMISSIONS_POLICY = {  
    "geolocation": [],  
    "autoplay": [],  
    "camera": [],  
    "microphone": [],  
    "payment": [],  
    "fullscreen": [],  
}

# Process register
Name: Nico Sergeyssels  
Address: Nijverheidskaai 170, 1080 Anderlecht  
Processing goal: To allow basic operation from site and authenticate the user  
Security measures: Watch security policy settings