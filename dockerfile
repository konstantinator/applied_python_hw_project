FROM python:3.10-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

#
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev

RUN pip install -U pip

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./main.py /code/main.py

# 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5555"]