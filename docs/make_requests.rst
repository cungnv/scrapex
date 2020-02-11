Make HTTP requests
==================

Send GET requests
::
    
    >>> from scrapex import Scraper
    >>> s = Scraper()
    >>> doc = s.load('https://github.com/search?q=scraping')
    >>> print(doc.response.status_code)
    200
    >>> print(doc.response.request.headers)
    {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36', 'Accept-Language': 'en-us,en;q=0.5', 'Accept-Encoding': 'gzip, deflate', 'Connection': 'keep-alive'}
    >>> 


Send POST requests
::
    
    >>> doc = s.load('http://httpbin.org/post', data={'name1':'value1', 'name2':'value2'})
    >>> doc.response.json()
    {'args': {}, 'data': '', 'files': {}, 'form': {'name1': 'value1', 'name2': 'value2'}, 'headers': {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-us,en;q=0.5', 'Content-Length': '25', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': 'httpbin.org', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36', 'X-Amzn-Trace-Id': 'Root=1-5e42296f-72e27fb04c47860421601594'}, 'json': None, 'origin': '42.114.13.13', 'url': 'http://httpbin.org/post'}
    >>>
    >>> doc = s.load('http://httpbin.org/post', data='name1=value1&name2=value2')
    >>> doc.response.json()
    {'args': {}, 'data': 'name1=value1&name2=value2', 'files': {}, 'form': {}, 'headers': {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-us,en;q=0.5', 'Content-Length': '25', 'Host': 'httpbin.org', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15', 'X-Amzn-Trace-Id': 'Root=1-5e4229f8-ce30254a99ad99202e50b612'}, 'json': None, 'origin': '42.114.13.13', 'url': 'http://httpbin.org/post'}
    >>> 

Send requests with custom headers
::
    >>> headers = {'Referer': 'https://github.com/?q=scraping',
    ...     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko)',
    ...     }
    >>> doc = s.load('https://github.com/cungnv/scrapex', headers=headers)
    >>>
    >>> doc.response.request.headers
    {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko)', 'Accept-Language': 'en-us,en;q=0.5', 'Accept-Encoding': 'gzip, deflate', 'Connection': 'keep-alive', 'Referer': 'https://github.com/?q=scraping', 'Cookie': '_octo=GH1.1.1947465757.1581393340; logged_in=no; _gh_sess=WjhnT0tOV2Nqa2xZRHVqY1VwWkgwckRMT3FJck03UWtlSThMYkdUVFNTYzBMNW5jcTYvd3NKbzhGR0Y3bUJhOFlUZkt1VWJNQ2UyWjJzL0FhMFprOTBVdTNEQzgraCtidE9IVnJhZ25sWXRKdHJhNUZZeEVNNWdDM3NZekg1YTRrQmlIakZEU21qWVVHc2N2OVRnM3ZBPT0tLVZVeWt6UTY4OEVzYm03S3pqY3dqaUE9PQ%3D%3D--85276db3b6db4db17aa5766f84e5251d8911f146'}
    >>> 



Failed requests
::
    
    >>> try:
    ...     doc = s.load('http://httpbin.org/status/404')
    ... except Exception as e:
    ...     print(type(e))
    ...     print('status code:', e.response.status_code)
    ... 
    <class 'requests.exceptions.HTTPError'>
    status code: 404
    >>> 


