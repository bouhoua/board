from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.paginator import Paginator

from article.models import User, Article
import hashlib

def index(request):
    return render(request, 'index.html')

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

def signout(request):
    del request.session['email'] # 개별 삭제
    request.session.flush() # 전체 삭제
    return HttpResponseRedirect('/index/')

def write(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        try:
            email = request.session['email']
            # select * from user where email = ?
            user = User.objects.get(email=email)
            # insert into article (title, content, user_id) values (?, ?, ?)
            article = Article(title=title, content=content, user=user)
            article.save()
            return render(request, 'write_success.html')
        except:
            return render(request, 'write_fail.html')

    return render(request, 'write.html')

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

def detail(request, id):
    # select * from article where id = ?
    article = Article.objects.get(id=id)
    
    context = {
        'article' : article
    }
    
    return render(request, 'detail.html', context)

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

