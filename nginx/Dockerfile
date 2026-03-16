FROM nginx:latest

# Install tzdata and set the timezone inside the container image
# This is necessary because on servers like EC2, the host might be in UTC
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
    echo "Asia/Kolkata" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*
