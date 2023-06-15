FROM python:3.10.10

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

RUN rm -f /etc/localtime \
&& ln -sv /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo "Asia/Shanghai" > /etc/timezone

RUN mkdir -p ~/.streamlit/ && touch ~/.streamlit/config.toml && echo '[server]\nmaxUploadSize=50' > ~/.streamlit/config.toml

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8081", "--server.address=0.0.0.0"]