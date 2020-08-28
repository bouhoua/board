from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from django.forms.models import model_to_dict

from map.models import Point
from article.models import User, Article
from email.mime.text import MIMEText

import smtplib
import hashlib
import math
import time

# 인덱스
def index(request):
    return render(request, 'index.html')

# 회원가입
def signup(request):
    if request.method == 'POST':
        # 회원정보 저장
        email = request.POST.get('email')
        name = request.POST.get('name')
        pwd = request.POST.get('pwd')

        # 암호화
        # m = hashlib.sha256()
        # m.update(bytes(pwd, encoding = "utf-8"))
        # pwd = m.hexdigest()
        
        user = User(email=email, name=name, pwd=pwd)
        user.save()
    
        return HttpResponseRedirect('/index/')
    
    return render(request, 'signup.html')

# 로그인
def signin(request):
    if request.method == 'POST':
        # 회원정보 조회
        email = request.POST.get('email')
        pwd = request.POST.get('pwd')

        try :
        # select * from user where email=? and pwd=?
            user = User.objects.get(email=email, pwd=pwd)
            # 세션 유지
            request.session['email'] = email
            
            return render(request, 'signin_success.html')
        except :
            return render(request, 'signin_fail.html')
    return render(request, 'signin.html')

# 로그아웃
def signout(request):
    del request.session['email'] # 개별 삭제
    request.session.flush() # 전체 삭제
    return HttpResponseRedirect('/index/')

# 글쓰기 only 회원
def write(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        try:
            email = request.session['email']
            # select * from user where email = ?
            user = User.objects.get(email=email)
            
            ####################################################################

            upload_file = request.FILES['upload_file']

            # 파일 저장
            # file = open('', '')
            # file.write('내용')
            file_name = upload_file.name
            
            # 만약 파일명이 중복되었으면 image.jpg
            # .의 위치를 찾아서 파일명이랑 확장자를 분리
            idx = file_name.find('.')

            file1 = file_name[0 : idx]      # image
            file2 = file_name[idx :]        # .jpg
            sep = time.time()               # unix time (ms)

            file_name = file1 + str(sep) + file2
            
            with open('article/static/' + file_name, 'wb') as file:
                # 파일 open 후 업로드 시 경로에서 맨 앞에 /가 붙어있으면 접근할 수 있는 하드 or 웹의 최상위 경로(절대 경로)
                # /가 맨 앞에 없으면 현재 디렉토리에서 출발하는 상대 경로
                # ex) with open('/home/' + file_name, 'wb') as file:
                for chunk in upload_file.chunks():
                    file.write(chunk)

            #####################################################################

            # insert into article (title, content, user_id) values (?, ?, ?)
            article = Article(title=title, content=content, user=user)
            article.file_name = '/static/' + file_name
            article.save()

            return render(request, 'write_success.html')
        except:
            return render(request, 'write_fail.html')

    return render(request, 'write.html')

# 글 목록
def list(request):
    page = request.GET.get('page')

    if not page :
        page = 1

    # select * from article order by id desc
    article_list = Article.objects.order_by('-id')

    p = Paginator(article_list, 10)
    page_info = p.page(page)

    context = {
        'article_list' : page_info,
        'num_list' : range(int(page_info.start_index()), int(page_info.end_index()))
    }
    
    return render(request, 'list.html', context)

# 글 세부내용
def detail(request, id):
    # select * from article where id = ?
    article = Article.objects.get(id=id)
    
    context = {
        'article' : article
    }
    
    return render(request, 'detail.html', context)

# 글 수정
def update(request, id):
    # select * from article where id = ?
    article = Article.objects.get(id = id)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        try:
            # update article set title = ?, content = ? where id = ?
            article.title = title
            article.content = content
            article.save()
            
            return render(request, 'update_success.html')
        except:
            return render(request, 'update_fail.html')
    context = {
        'article' : article
    }
    
    return render(request, 'update.html', context)

# 글 삭제
def delete(request, id):
    try:
        # select * from article where id = ?
        article = Article.objects.get(id=id)
        article.delete()
        
        return render(request, 'delete_success.html')
    except:
        return render(request, 'delete_fail.html')

def test(request) :
    u = User.objects.get(id = 2)
    for i in range(100) :   # range는 list 구조 반복문 범위 설정할 때도 사용 가능
        Article(title = '제목-%s' % i, content ='내용-%s' % i, user = u).save()

    return HttpResponse('done')

# 지도
def map(request) :
    return render(request, 'map.html')

# 위치 정보
def map_data(request):
    data = Point.objects.all()
    
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    map_list = []
    
    for d in data :
        d = model_to_dict(d) # QuerySet -> Dict

        dist = distance(float(lat), float(lng), d['lat'], d['lng'])
        
        if(dist <= 10): # 10km 이내의 장소만 응답결과로 저장
            map_list.append(d)
    # dict가 아닌 자료는 항상 safe=False 옵션 사용
    return JsonResponse(map_list, safe = False)

# 거리 구하기
def distance(lat1, lng1, lat2, lng2) :
    theta = lng1 - lng2

    dist1 = math.sin(deg2rad(lat1)) * math.sin(deg2rad(lat2))
    dist2 = math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2))
    dist2 = dist2 * math.cos(deg2rad(theta))

    dist = dist1 + dist2
    dist = math.acos(dist)
    dist = rad2deg(dist) * 60 * 1.1515 * 1.609344

    return dist

def deg2rad(deg):
    return deg * math.pi / 180.0

def rad2deg(rad):
    return rad * 180.0 / math.pi

# 네비바 컨택트 연결
def contact(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        comment = request.POST.get('comment')
        # 발신자주소, 수신자주소, 메시지
        send_mail('HarryPotter@gmail.com', email, comment)
        return render(request, 'contact_success.html')
    return render(request, 'contact.html')

# 메일 보내기
def send_mail(from_email, to_email, msg):
    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465) # SMTP 설정
    smtp.login(from_email, '****************') # 인증정보 설정 => 앱 비밀번호 16 자리
    
    msg = MIMEText(msg)
    msg['Subject'] = '[문의사항]' + to_email # 제목
    msg['To'] = from_email # 수신 이메일
    
    smtp.sendmail(from_email, from_email, msg.as_string())
    smtp.quit()

# 파일 업로드
def upload(request) :
    if request.method == 'POST' :
        upload_file = request.FILES['upload_file']

        # 파일 저장
        # file = open('', '')
        # file.write('내용')
        file_name = upload_file.name
        
        # 만약 파일명이 중복되었으면 image.jpg
        # .의 위치를 찾아서 파일명이랑 확장자를 분리
        idx = file_name.find('.')

        file1 = file_name[0 : idx]      # image
        file2 = file_name[idx :]        # .jpg
        sep = time.time()               # unix time (ms)

        file_name = file1 + str(sep) + file2
        
        with open('article/static/' + file_name, 'wb') as file:
            # 파일 open 후 업로드 시 경로에서 맨 앞에 /가 붙어있으면 접근할 수 있는 하드 or 웹의 최상위 경로(절대 경로)
            # /가 맨 앞에 없으면 현재 디렉토리에서 출발하는 상대 경로
            # ex) with open('/home/' + file_name, 'wb') as file:
            for chunk in upload_file.chunks():
                file.write(chunk)
            
        return HttpResponse(upload_file.name)
        
    return render(request, 'upload.html')

