FROM ghcr.io/bubuntux/nordvpn:v3.12.2
RUN apt update && apt install wget python3-pip -y
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >>/etc/apt/sources.list.d/google.list
RUN apt update && apt -y install google-chrome-stable

WORKDIR /src
COPY . .

# Install Python deps
RUN pip install -r requirements.txt

# START
CMD nord_login && nord_config && nord_connect && python3 start.py
