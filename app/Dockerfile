FROM docker.arvancloud.ir/python:3.11-slim

WORKDIR /app

# کپی کردن فایل نیازمندی‌ها و پوشه ویل‌ها به داخل کانتینر
COPY requirements.txt .
COPY wheels/ /wheels/

# نصب کاملاً آفلاین و لوکال از روی پوشه wheels بدون نیاز به اینترنت
RUN pip install --no-index --find-links=/wheels/ -r requirements.txt

# کپی کردن بقیه فایل‌های پروژه
COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
