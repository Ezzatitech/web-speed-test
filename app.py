import requests
import time
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import datetime
from collections import deque

def measure_load_time(url):
    result = {"url": url, "success": False}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    start_time = time.time()
    response = None

    try:
        if not url.startswith(('http://', 'https://')):
            temp_url_https = f"https://{url}"
            try:
                requests.head(temp_url_https, timeout=5, headers=headers, allow_redirects=True)
                url = temp_url_https
            except requests.exceptions.RequestException:
                url = f"http://{url}"
        result['url'] = url

        response = requests.get(url, timeout=15, stream=True, headers=headers, allow_redirects=True)
        response.raise_for_status()

        ttfb_approx = response.elapsed.total_seconds()
        content = response.content
        end_time = time.time()
        total_load_time = end_time - start_time

        content_size = len(content)
        page_title = "یافت نشد"
        try:
            if 'text/html' in response.headers.get('Content-Type', '').lower():
                 soup = BeautifulSoup(content, 'html.parser')
                 if soup.title and soup.title.string:
                     page_title = soup.title.string.strip()
        except Exception:
            page_title = "خطا در خواندن عنوان"

        result.update({
            "success": True,
            "time": total_load_time,
            "ttfb_approx": ttfb_approx,
            "content_size": content_size,
            "status_code": response.status_code,
            "page_title": page_title,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return result

    except requests.exceptions.Timeout:
        result['error'] = "درخواست زمان‌بر شد (Timeout)."
    except requests.exceptions.HTTPError as http_err:
         result['error'] = f"خطای HTTP: {http_err.response.status_code}"
         if http_err.response is not None:
             result['status_code'] = http_err.response.status_code
    except requests.exceptions.ConnectionError:
         result['error'] = "خطای اتصال. آیا آدرس یا اینترنت درست است؟"
    except requests.exceptions.RequestException as e:
        result['error'] = f"خطای درخواست: {e}"
    except Exception as e:
         result['error'] = f"خطای پیش‌بینی نشده: {e}"

    if 'error' in result:
        result["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return result


app = Flask(__name__)
test_history = deque(maxlen=10)

@app.route('/', methods=['GET', 'POST'])
def index():
    result_data = None
    current_history = list(test_history)

    if request.method == 'POST':
        url_to_test = request.form.get('url')
        if url_to_test:
            result_data = measure_load_time(url_to_test.strip())
            test_history.appendleft(result_data)
            current_history = list(test_history)

    return render_template('index.html', result=result_data, history=current_history)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')