import requests
import bs4
import sys
import time
from func_timeout import func_set_timeout
from multiprocessing.dummy import Pool
start_time_main=time.time()

# 配置项目
global headers,origin_list,real_list,domain_list,page_deep,count,count_2,target_not_run
origin_list=[] # 百度搜索的结果的原始超链接
real_list=[] # 百度搜索的结果的真实超链接
domain_list=[] # 保存传入的子域名
page_deep=100 # 爬取的页数
count=0 # 计数器
count_2=0
target_not_run=[]
headers={
    
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cookie": "BAIDUID={your BAIDUID}:FG=1; BIDUPSID={your BIDUPSID}; BDORZ={BDORZ}; PSTM=1584264211; delPer=0; BD_CK_SAM=1; PSINO=3; H_PS_PSSID=30975_1435_21094_30842_30824_26350_30717; BD_UPN=12314353; H_PS_645EC=5444UcMDlyCN5adXuqZxiDLdafBYTTQrvxrBsUxzl6LXR6JNAma5isZCfPc"
    }


# 检测是否触发了百度第一层反爬机制
def is_baidu_spider_ok(r):
    if isinstance(r,requests.models.Response):
        if len(r.text)>100000:
            print(r.request.url,"绕过了一层反爬机制")
            return True
        else:
            print("触发了一层反爬机制，请重新配置")
            return False
    else:
        print("请传入一个requests实例")
        return False

# 百度爬虫,传入（关键字，页数），将原始链接添加到origin_list中,用了超时装饰器之后，抛出异常会卡死，所以
def get_url(domain_page):
    try:
        get_url0(domain_page)
    except:
        pass

@func_set_timeout(5)
def get_url0(domain_page):
    global target_not_run
    global count
    if domain_page in target_not_run:
        exit()
    start_time_inner = time.time()
    baidu_search_url = 'https://www.baidu.com/s?wd='+domain_page[0]+'&pn='+str((domain_page[1])*10)
    try:
        baidu_search_req = requests.get(baidu_search_url,headers=headers)
        is_baidu_spider_ok(baidu_search_req)
        baidu_search_bs = bs4.BeautifulSoup(baidu_search_req.text, "lxml")
        a_bs = baidu_search_bs.find_all("a", class_="c-showurl")
        print("共发现",len(a_bs),"个结果")

        # 如果发现某一页的结果为0，那么后续的页也就不跑了，但是无法取消现在正在跑的~
        
        if len(a_bs)==0:
            for page in range(domain_page[1],page_deep):
                target_not_run.append((domain_page[0],page))
            target_not_run=list(set(target_not_run))
        
        # 获取当前页面的原始链接，形如“http://www.baidu.com/link?url=gO7UsA_Q5oAGHPW8WiI5Dy-wuesK1AFl5QYEJ5mcv71DnUGKbCj2-sVCuk--BLeI5uWd7qgmwQU448d8ODlQRZUN6aRBB28-_IaODdi3fQLT58p1ZYLGbAqHCU9T0tt_”
        # 并且把原始链接添加到origin_list中
        for _ in range(len(a_bs)):
            __ = eval(a_bs[_].next_sibling["data-tools"])['url']
            #print(__)
            origin_list.append(__)
    except Exception as e:
        print("获取原始链接的过程出错:",e)
    end_time_inner = time.time()
    count=count-1
    print("总共剩余",count,"次请求")
    print('获取原始链接共耗时:',str(end_time_inner-start_time_inner),'秒')

# 生成用于传入get_url中的元组
def make_payload(domain_list,page_counts):
    _=[]
    for domain in domain_list:
        for page in range(page_counts):
            _.append(("site:"+domain+" inurl:=",page))
            _.append(("site:"+domain+" inurl:-",page))
            _.append(("site:"+domain+" inurl:_",page))
            _.append(("site:"+domain+"",page))
    return _

# 将原始超链接转化为真实超链接
def origin_to_real(link):
    try:
        origin_to_real0(link)
    except:
        pass
@func_set_timeout(5)
def origin_to_real0(link):
    global count_2
    start_time_inner = time.time()
    try:
        origin_req=requests.get(link,headers=headers,allow_redirects=False)
        real_list.append(origin_req.headers['Location'])
        # print(origin_req.headers['Location'])
    except Exception as e:
        print("原始超链接转化为真实超链接出错:",e)
    end_time_inner = time.time()
    count_2=count_2-1
    print('原始超链接转化为真实超链接共耗时:',str(end_time_inner-start_time_inner),'秒')
    print("总共剩余",count_2,"次请求")

# 读取子域名文件
def get_subdomains(file_name):
    with open(file_name,encoding="utf-8") as f:
        for _ in f.readlines():
            if _ != "\n":
                domain_list.append(_.strip().split(" ")[0])

# 把一个列表的链接全部保存到指定的文件中
def save_list_to_file(list_name):
    file_name=time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))
    with open(str(file_name)+".txt","w",encoding="utf-8") as f:
        for _ in list_name:
            f.write(_+"\n")
        

# 开始主逻辑
if __name__=='__main__':
    # 读取子域名文件
    get_subdomains(sys.argv[1])
    
    # 生成用于传入get_url中的元组,形如[('site:m.xyz.cn inurl:=', 0), ('site:m.xyz.cn inurl:-', 0), ('site:m.xyz.cn inurl:_', 0), ('site:m.xyz.cn inurl:=', 1), ('site:m.xyz.cn inurl:-', 1), ('site:m.xyz.cn inurl:_', 1), ('site:m.suning.com inurl:=', 0), ('site:m.suning.com inurl:-', 0), ('site:m.suning.com inurl:_', 0), ('site:m.suning.com inurl:=', 1), ('site:m.suning.com inurl:-', 1), ('site:m.suning.com inurl:_', 1)]
    target=make_payload(domain_list,page_deep)
    
    # 打印
    count=len(target)
    print("获取原始链接中，预计进行",count,"次请求")
    # print(target)
    # 获取原始超链接
    with Pool(100) as p:
        p.map(get_url,target)
    count_2=len(origin_list)
    # 将原始超链接转化为真实超链接
    print("将原始超链接转化为真实超链接")
    with Pool(100) as p1:
        p1.map(origin_to_real,origin_list)
    # print(real_list)

    # 保存真实超链接
    save_list_to_file(list(set(sorted(real_list))))

    end_time_main=time.time()
    
    print("程序共耗时",end_time_main-start_time_main,"秒")
