# -*- coding:utf-8 -*-
import datetime
from bs4 import BeautifulSoup
import requests
import smtplib
from email.mime.text import MIMEText
import sqlite3
from apscheduler.schedulers.blocking import BlockingScheduler



#===========================================================================
def crawling(url,page,conn,cur):

    # requests로 페이지 가져오기
    text = requests.get(url+str(page)).text

    # bs로 파싱
    bs_obj = BeautifulSoup(text,'html.parser')

    # 핫딜 게시글 선택
    trs = bs_obj.select('#board_list > div > div.board_main.theme_default > table > tbody > tr')

    # 빈 메시지 생성
    message = ''


    # 핫딜 게시글 제목과 url을 빈 메시지에 추가
    for tr in reversed(trs[3:]):
        id = tr.find('td',{'class':'id'}).text.strip()
        id2 = cur.execute('SELECT board_id FROM Pages WHERE board_id =?',[id]).fetchone()

        if id2 == None:
            type = tr.find('td',{'class':'divsn'}).text.strip()
            name = tr.find('a',{'class':'deco'}).text.strip()
            author = tr.find('td',{'class':'writer'}).text.strip()
            recommend = tr.find('td',{'class':'recomd'}).text.strip()
            if recommend =='':
                recommend = 0
            view = tr.find('td',{'class':'hit'}).text.strip()
            url = tr.find('a',{'class':'deco'})['href']
            print(name)
            # DB에 데이터 입력
            cur.execute('INSERT OR IGNORE INTO Pages (board_id,type,subject,author,recommend,view,url) VALUES (?,?,?,?,?,?,?)',(id,type,name,author,recommend,view,url))
            # 변경내용 저장
            conn.commit()
            message = message+name+'\n'+url+'\n'+'\n'
        else:
            if int(id) == id2[0]:
                continue
            else:
                type = tr.find('td',{'class':'divsn'}).text.strip()
                name = tr.find('a',{'class':'deco'}).text.strip()
                author = tr.find('td',{'class':'writer'}).text.strip()
                recommend = tr.find('td',{'class':'recomd'}).text.strip()
                if recommend =='':
                    recommend = 0
                view = tr.find('td',{'class':'hit'}).text.strip()
                url = tr.find('a',{'class':'deco'})['href']
                print(name)
                # DB에 데이터 입력
                cur.execute('INSERT OR IGNORE INTO Pages (board_id,type,subject,author,recommend,view,url) VALUES (?,?,?,?,?,?,?)',(id,type,name,author,recommend,view,url))
                # 변경내용 저장
                conn.commit()
                message = message+name+'\n'+url+'\n'+'\n'

    return message,id

#===========================================================================

# 핫딜 목록 메일 보내는 함수 정의
def send_mail(id,pw,to,mssg):
    # SMTP연결
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()      # extended hello SMTP확장 목록 요청
    smtp.starttls()  # G메일은 tls인증을 사용하기 때문에 tls인증 함수 호출
    smtp.login(id, pw) # 메일계정 로그인

    # 메일 본문
    msg = MIMEText(mssg)
    # 메일 제목
    msg['Subject'] = '루리웹핫딜'
    # 수신자
    msg['To'] = to

    # 메일 보내기
    smtp.sendmail(id, to, msg.as_string())

    # 메일 전송 종료
    smtp.quit()

#===========================================================================
def start_crawler():
    # 루리웹 핫딜게시판 주소
    url = 'http://bbs.ruliweb.com/market/board/1020?page='
    # 핫딜게 페이지 지정
    page = 1

    # db파일 생성
    conn = sqlite3.connect('hotdeal.sqlite')
    # 커서 생성
    cur = conn.cursor()
    # 테이블 생성
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Pages (
        board_id INTEGER UNIQUE,
        type TEXT,
        subject TEXT,
        author TEXT,
        recommend INTEGER,
        view INTEGER,
        url TEXT
    )''')
    print(datetime.datetime.now())
    print('크롤링 시작')
    message,id = crawling(url,page,conn,cur)
    if message == '':
        print(message)
        print('새로운 핫딜이 없습니다.\n')
    else:
        # 구글 아이디
        mail_id = '*******'
        # 구글 비밀번호
        mail_pw = '*******'
        # 수신자 메일 주소
        to_mail = '*******@naver.com'

        print('메일 전송')
        send_mail(mail_id,mail_pw,to_mail,message)
        print('전송 완료')


# 1시간 간격으로 크롤러 실행
sched = BlockingScheduler()
sched.add_job(start_crawler,'interval', hours=1)
sched.start()
