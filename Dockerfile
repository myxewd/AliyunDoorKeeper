FROM python:3.13-slim

WORKDIR /app

COPY . /app

# If you are in a different time zone, you can also set it by mounting localtime
# docker run -v /etc/localtime:/etc/localtime:ro -v /etc/timezone:/etc/timezone:ro aliyundk

RUN apt-get update && apt-get install -y tzdata
ENV TZ=Asia/Shanghai
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 6082

CMD ["python", "run.py"]
