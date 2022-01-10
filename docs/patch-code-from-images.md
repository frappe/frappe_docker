Example: https://discuss.erpnext.com/t/sms-two-factor-authentication-otp-msg-change/47835

Above example needs following Dockerfile based patch

```Dockerfile
FROM frappe/erpnext-worker:v12.17.0

RUN install_app custom_app https://github.com/username/custom_app version-12
RUN sed -i -e "s/Your verification code is/আপনার লগইন কোড/g" /home/frappe/frappe-bench/apps/frappe/frappe/twofactor.py
```
