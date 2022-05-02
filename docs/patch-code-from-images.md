Example: https://discuss.erpnext.com/t/sms-two-factor-authentication-otp-msg-change/47835

Above example needs following Dockerfile based patch

```Dockerfile
FROM frappe/erpnext-worker:v12.17.0

...
USER root
RUN sed -i -e "s/Your verification code is/আপনার লগইন কোড/g" /home/frappe/frappe-bench/apps/frappe/frappe/twofactor.py
USER frappe
...

```

Example for `nginx` image,

```Dockerfile
FROM frappe/erpnext-nginx:v13.27.0

# Hack to use Frappe/ERPNext offline.
RUN sed -i 's/navigator.onLine/navigator.onLine||true/' \
  /usr/share/nginx/html/assets/js/desk.min.js \
  /usr/share/nginx/html/assets/js/dialog.min.js \
  /usr/share/nginx/html/assets/js/frappe-web.min.js
```

Alternatively copy the modified source code file directly over `/home/frappe/frappe-bench/apps/frappe/frappe/twofactor.py`

```Dockerfile
...
COPY twofactor.py /home/frappe/frappe-bench/apps/frappe/frappe/twofactor.py
...
```
