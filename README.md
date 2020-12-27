# Slack App for ipTIME

This Slack App is for management of ipTime - Specially firewall setting (Internet/WiFi Usage Restriction)

This repository comes from my blog posts
  - [ipTIME 원격 관리하기#1 : 관리 App 사용 vs. 크롤링 사용](https://gomeisa-it.tistory.com/5?category=438469)
  - [ipTIME 원격 관리하기#2 : 크롤링으로 설정 변경하기](https://gomeisa-it.tistory.com/6?category=438469)
  - [ipTIME 원격 관리하기#3 : Slack 을 이용하여 설정 변경하기](https://gomeisa-it.tistory.com/7?category=438469)

## Installation
```bash
$ pip install -r requirements.txt
```

## Configuration
In code, set your own configurations
```
iptime_ip = "192.168.100.1"  # your ipTIME Web IP
iptime_user = "login-user"  # your ipTIME Login ID
iptime_password = "login-password"  # your ipTIME Login Password
token = "xoxb-your-slackapp-token"  # your Slack App token
port = 8787  # your Slack App Request URL port
```
## Run
```bash
$ python3 slackapp-iptime.py
```