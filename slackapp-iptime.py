import re
import requests

from bs4 import BeautifulSoup
from collections import OrderedDict
from flask import Flask
from slackify import Slackify, Slack, reply_text

# set your own configurations ---------->
iptime_ip = "192.168.100.1"  # your ipTIME Web IP
iptime_user = "login-user"  # your ipTIME Login ID
iptime_password = "login-password"  # your ipTIME Login Password
token = "xoxb-your-slackapp-token"  # your Slack App token
port = 8787  # your Slack App Request URL port
# <--------------------------------------

app = Flask(__name__)
slackify = Slackify(app=app)
slack = Slack(token)


def login(name, password):
    # 이 정보는 지워도 된다
    cookies = {
        'efm_session_id': 'HBds7VZi8SD58UXD',
    }

    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'http://%s' % iptime_ip,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'http://%s/sess-bin/login_session.cgi' % iptime_ip,
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    data = {
        'init_status': '1',
        'captcha_on': '0',
        'captcha_file': '',
        'username': name,  # 실제 id 정보
        'passwd': password,  # 실제 password 정보
        'default_passwd': '\uCD08\uAE30\uC554\uD638:admin(\uBCC0\uACBD\uD544\uC694)',
        'captcha_code': ''
    }

    response = requests.post('http://%s/sess-bin/login_handler.cgi' % iptime_ip,
                             headers=headers,
                             cookies=cookies,
                             data=data,
                             verify=False)

    # cookie 정보를 읽어온다
    p = re.compile(r"setCookie\('(.*)'\);")
    f = p.findall(response.text)

    cookies = {
        'efm_session_id': f[0]
    }

    return cookies


def get_ap_info(cookies):
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'http://%s/sess-bin/login_handler.cgi' % iptime_ip,
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    response = requests.get('http://%s/sess-bin/login.cgi' % iptime_ip,
                            headers=headers,
                            cookies=cookies,
                            verify=False)

    if 200 == response.status_code:
        soup = BeautifulSoup(response.text, "html.parser")

        # regexp
        regexp_model_name = re.compile(r"^ipTIME\s+(.*)$")
        regexp_external_ip = re.compile(r"(\d+.\d+.\d+.\d)")
        regexp_version = re.compile(r"^Version\s+(.*)")

        try:
            model = regexp_model_name.findall(soup.title.text)[0]
        except IndexError:
            model = soup.title.text

        parse_data = soup.find_all("span")

        external_ip = regexp_external_ip.findall(parse_data[0].text)[0]
        version = regexp_version.findall(parse_data[1].text)[0]

        return {
            "model": model,
            "external_ip": external_ip,
            "version": version
        }


def get_firewalls(cookies):
    keys = [
        "mode",
        "name",
        "src_addr_type",
        "src_start",
        "src_end",
        "dest_addr_type",
        "dest_start",
        "dest_end",
        "sport",
        "eport",
        "direction",
        "protocol",
        "policy",
        "days",
        "stime",
        "etime",
        "disabled",
        "priority"
    ]

    headers = {
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'http://%s/sess-bin/timepro.cgi?tmenu=firewallconf&smenu=firewall' % iptime_ip,
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    params = (
        ('tmenu', 'iframe'),
        ('smenu', 'firewall'),
        ('mode', 'all'),
    )

    response = requests.get("http://%s/sess-bin/timepro.cgi" % iptime_ip,
                            headers=headers,
                            params=params,
                            cookies=cookies,
                            verify=False)

    soup = BeautifulSoup(response.text, "html.parser")

    firewalls = OrderedDict()

    # 위의 두번째 image 에서 참조된 html 객체로 전체 firewall 정보를 얻는다
    for tr in soup.find_all("tr", class_="fw_tr")[:-2]:
        firewall = {}
        values = eval(tr.attrs["onclick"].replace("onClickedFWRule",
                                                  "").replace("true",
                                                              "True").replace("false",
                                                                              "False")[:-1])
        for k, v in zip(keys, values):
            firewall[k] = v

        firewalls[firewall["name"]] = firewall

    return firewalls


def set_firewall(cookies, firewall, off):
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'http://%s' % iptime_ip,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'http://%s/sess-bin/timepro.cgi' % iptime_ip,
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    # 새로운 6개의 key 를 설정한다
    data = {
        'tmenu': 'iframe',
        'smenu': 'firewall',
        'act': 'modify',
        'view_mode': 'all',
        'old_priority': firewall['priority'],
        'band': ''
    }

    # 기존 firewall 정보를 추가 (update) 한다
    data.update(firewall)

    # 규칙비활성화 (설정 on/off) 하는 값을 설정한다
    data['disabled'] = int(off)

    response = requests.post('http://%s/sess-bin/timepro.cgi' % iptime_ip,
                             headers=headers,
                             cookies=cookies,
                             data=data,
                             verify=False)


@slackify.command
def iptime(command_args, response_url):
    firewalls = get_firewalls(login(iptime_user, iptime_password))

    text = ""
    text_on_off = ""

    try:
        priority = int(command_args)
    except ValueError:  # parameter 가 없거나 원치않는 값이 들어왔을 경우
        priority = -1

    for name, firewall in firewalls.items():
        if firewall["priority"] == priority:  # 없는 priority (index) 인 경우는 no hit
            firewall["disabled"] = not firewall["disabled"]
            # 설정
            set_firewall(login(iptime_user, iptime_password), firewall, firewall["disabled"])
            text_on_off = "\n\n*[{}]* is _{}_".format(name, "off" if firewall["disabled"] else "on")

        state = ":black_square_button:" if firewall["disabled"] else ":ballot_box_with_check:"
        text += f"{state} {firewall['priority']} {name}\n"

    return reply_text(text + text_on_off)


if "__main__" == __name__:
    app.run(host="0.0.0.0", port=port, debug=True)
