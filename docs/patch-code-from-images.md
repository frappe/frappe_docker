Example: https://discuss.erpnext.com/t/sms-two-factor-authentication-otp-msg-change/47835

Above example needs following Dockerfile based patch

```Dockerfile
FROM frappe/erpnext-worker:v12.17.0

RUN /home/frappe/frappe-bench/env/bin/pip -e /home/frappe/frappe-bench/apps/custom_app
RUN sed -i -e "s/Your verification code is/আপনার লগইন কোড/g" /home/frappe/frappe-bench/apps/frappe/frappe/twofactor.py
```
