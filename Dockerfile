FROM python:3.11-buster

WORKDIR /app

RUN pip install pipenv
COPY src/Pipfile.lock /app
COPY src/Pipfile /app
RUN pipenv install --system --deploy --ignore-pipfile

COPY src/ /app

ENTRYPOINT ["make", "python"]
