from bs4 import BeautifulSoup
import urllib.request as req
import requests
import datetime
from flask import Flask, render_template,request,redirect
from basic import db_connect,only_code_made, time_format
from inquiry import stock_inquiry, rate_import
import portfolio as p

#컨 R 누르면 매수 계속되는거 고쳐야함...
#로그인도 나중에 구현하여 사용자마다 DB가지게 해야함
COSPI,KOSDAQ = db_connect()
nowDATE = time_format()
app = Flask("Finance Portfolio")


#로그인 구현
@app.route('/login_confirm', methods=['POST'])
def login_confirm():
    id_ = request.form['id_']
    pw_ = request.form['pw_']
    if (id_ == 'admin' and pw_ == 'admin') or (id_ == 'user' and pw_ == 'user'):
        session['id'] = id_
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))








#대표 화면
@app.route("/")
def home():
    return render_template("mainpage.html")
#오늘의 시세 종목 검색
@app.route("/search")
def search():
    return render_template("search.html")
#오늘의 시세 출력
@app.route("/today_rate")
def today_rate():
    stock_item = request.args.get('stock_item')
    if stock_item in COSPI or KOSDAQ:
        code = only_code_made(COSPI, KOSDAQ, stock_item)
        stock_rate = stock_inquiry(stock_item, code, nowDATE)
    else:
        return redirect("/")
    return render_template("today_rate.html",searchingBy=stock_item,stockRate=stock_rate)
#종목 수익률 검색
@app.route("/stock_search")
def stock_search():
    return render_template("stock_search.html")
#종목 수익률 출력
@app.route("/stock_return")
def stock_return():
    try:
        stocks = request.args.get('stocks')
        if stocks in COSPI or KOSDAQ:
            code = only_code_made(COSPI, KOSDAQ, stocks)
            firstdate = request.args.get('purchase_date')
            lastdate = request.args.get('sale_date')
            stocks,firstdate,lastdate,profit = rate_import(code, firstdate, lastdate, stocks, nowDATE)
        else:
            return redirect("/")
        return render_template("stock_return.html",stockItem=stocks,purDate=firstdate,saleDate=lastdate,Profit = profit)
    except:
        return redirect("/")

#포트폴리오 선택 화면 1.매수 2.매도 3.포트폴리오 조회 4.매도수익 5.초기화
@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")

#종목 매수 정보 입력
@app.route("/portfolio_buy")
def portfolio_buy():
    return render_template("portfolio_buy.html")
#매수 완료
@app.route("/portfolio_buy_return")
def portfolio_buy_return():
    get_buycollect = p.buy_open()
    name = request.args.get('name')
    check = None
    if name in COSPI or KOSDAQ:
        code = only_code_made(COSPI, KOSDAQ, name)
        price = request.args.get('price')
        number = request.args.get('number')
        #이미 매수한 종목인지 확인
        if(name in get_buycollect):
            #매수한 경우 원래 값 수정
            p.buy_correct(name, price, number, get_buycollect)
            check = 1
        else:
            #새로 저장
            p.buy_save(name, price, number)
            check = 2
    else:
        return redirect("/")
    return render_template("portfolio_buy_return.html",check=check)

#종목 매도 정보 입력
@app.route("/portfolio_sell")
def portfolio_sell():
    return render_template("portfolio_sell.html")

#종목 매도 완료
@app.route("/portfolio_sell_return")
def portfolio_sell_return():
    buycollect = p.buy_open()
    sellname = request.args.get('name2')
    sellprice = request.args.get('price2')
    sellnumber = request.args.get('number2')
    check = 0
    if sellname in COSPI or KOSDAQ:
        for i in range(0,len(buycollect)):
            if(buycollect[i] == sellname):
                saveprice = buycollect[i+1]
                savenumber = buycollect[i+2]
                remainprice = int(sellprice) - int(saveprice)
                #매도량과 종목이름 저장
                p.stock_item_save(sellname, sellnumber)
                #매도량이 매수량보다 많은지 확인
                checkcode = p.stock_item_check(sellname, savenumber)
            else:
                pass
            #정상
        if(checkcode == 1):
            #매도한 정보 저장
            p.sell_save(sellname, sellprice, sellnumber)
            #수익률 정보 저장
            p.profit_and_loss(sellname, saveprice, sellprice, remainprice, sellnumber)
            check =1
        #매도량이 매수량을 넘음
        else:
            #추가되어서 넘친 매도량 삭제
            p.stock_item_correct(sellname)
            print("알림 : <매도 수량을 다시입력해주세요>")
    else:
        return redirect("/")
    return render_template("portfolio_sell_return.html",checkcode = check)

#포트폴리오 출력
@app.route("/portfolio_inquiry")
def portfolio_inquiry():
    #초기 리스트 생성
    global p
    Buyitem= []
    get_code = []
    get_profit = []
    get_presentrate = []
    get_presentprofit = []
    Buyremain=[]
    sell_already=[]
    ptotal=[]
    ltotal=[]
    last_total=0
    present_total=0
    longline = "========================================================"
    #매수 정보 불러옴
    Buyinfor = p.buy_open()
    Sellinfor = p.sell_open()
    Size = len(Buyinfor) / 3
    for i in range(0,int(Size)):
        #매수 종목을 리스트에 저장
        Buyitem.append(Buyinfor[3*i])
    for i in range(0,len(Buyitem)):
        for j in range(0,len(Buyinfor)):
            #종목 이름이 들어있는 항목의 위치를 찾음
            if(Buyitem[i] == Buyinfor[j]):
                #매도한 내용이 있는지 확인
                if(len(Sellinfor) != 0):
                    for s in range(0,len(Sellinfor)):
                        if(Buyinfor[j] == Sellinfor[s]):
                            if(Sellinfor[s] not in sell_already):
                                #해당 종목의 매도량을 저장함
                                stocknumber = p.stock_item_open(Buyitem[i])
                                #현재 남은 수량을 저장함
                                Buyremain = int(Buyinfor[j+2]) - stocknumber
                                #리스트에 최신화(리스트를 이용하여 출력할 것이기 때문이다.)
                                Buyinfor[j+2] = Buyremain
                                sell_already.append(Sellinfor[s])
                                #코드만 불러옴
                            else:
                                pass
                        else:
                            Buyremain = Buyinfor[j+2]
                else:
                    #매도 내용이 없으면 현재 수량을 남은 수량으로 저장
                    Buyremain = Buyinfor[j+2]
                #최종적으로 종목을 출력 형식에 맞게 값을 변형시킴
                get_code = only_code_made(COSPI,KOSDAQ,Buyitem[i])   
                get_profit, get_presentrate, get_presentprofit,get_ptotal,get_ltotal = p.present_rate(get_code,Buyitem[i],Buyinfor[j+1],Buyremain) 
                ptotal.append(get_ptotal)
                ltotal.append(get_ltotal)
                Buyinfor.insert(j+2,get_presentrate)
                Buyinfor.insert(j+3,get_profit)
                Buyinfor.insert(j+5,get_presentprofit)
                Buyinfor.insert(j+6,longline)
            else:
                pass
    for l in range(0, len(Buyinfor)):
        if(Buyinfor[l] == 0):
            #만약 남은 수량이 0이라면 해당 정보가 출력되지 않게 삭제함
            del Buyinfor[l-4:l+3]
            break
        else:
            pass

    #입력된 내용을 형식적으로 다듬는 과정
    for k in range(0,len(Buyinfor)):
        if(k%7 == 1 ):
            average_rate = Buyinfor[k]
            get_average = format(int(average_rate),',')
            average = "평단가 : "+ get_average+"원"
            Buyinfor[k] = average
        elif(k%7 == 4):
            amount = Buyinfor[k]
            get_amount = format(int(amount),',')
            stock_amount = "수량 : " + get_amount+"주"
            Buyinfor[k] = stock_amount
        else:
            pass
    #총합 값 계산
    for n in range(0,len(ltotal)):
        last_total += ltotal[n] 
        present_total += ptotal[n] 
    #형식에 맞게 값 저장
    get_latotal = format(last_total,',')
    get_prtotal = format(present_total,',')
    if(present_total-last_total== 0):
        Buyinfor.append("구매 총합 : "+get_latotal+"원")
        Buyinfor.append("현재 총합 : "+get_prtotal+"원")
    else:
        total_profit = (present_total-last_total)/last_total*100
        Buyinfor.append("구매 총합 : "+get_latotal+"원")
        Buyinfor.append("현재 총합 : "+get_prtotal+"원")
        Buyinfor.append("총 수익률 : "+"{:0,.2f}".format(total_profit)+"%")
    portfolio_len =len(Buyinfor)
    return render_template("portfolio_inquiry.html",portfolio=Buyinfor,portfolio_len=portfolio_len)

#매도 수익 출력
@app.route("/portfolio_return")
def portfolio_return():
    PLcollect = p.pl_open()
    if PLcollect:
        length = len(PLcollect)
    else:
        return redirect("/")
    return render_template("/portfolio_return.html",PLcollect=PLcollect,len=length)

#포트폴리오 초기화 여부 확인
@app.route("/portfolio_init")
def portfolio_init():
    return render_template("/portfolio_init.html")

#포트폴리오 초기화
@app.route("/portfolio_init_return")
def portfolio_init_return():
    initialize = request.args.get('initialize')
    if(initialize=="초기화"):
        stock_item = p.buy_open()
        p.portfolio_initialize(stock_item)
    else:
        pass
    return render_template("/portfolio_init_return.html",initialize=initialize)


app.run(host='0.0.0.0')