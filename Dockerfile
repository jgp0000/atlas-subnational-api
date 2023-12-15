FROM python:3.8

LABEL maintainer="Julian Gil <julianlgil@hotmail.com.com>" version="1.0.0"

# Requirements are installed here to ensure they will be cached.
COPY . .
RUN pip3 install -r ../requirements-dev.txt
ENV FLASK_CONFIG="../conf/dev.py"
RUN sed -i 's/\r//' /start
RUN chmod +x /start
CMD ["/start"]