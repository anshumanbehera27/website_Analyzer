from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
import socket
import dns.resolver
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def fetch_external_resources(url):
    max_retries = 5
    retry_delay = 2  # Start with a 2-second delay

    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                html_content = response.text
                break
            elif response.status_code == 429:
                print(f"Rate limited. Attempt {attempt + 1} of {max_retries}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                return None, f"Failed to fetch URL. Status code: {response.status_code}"
        except Exception as e:
            return None, str(e)
    else:
        return None, "Exceeded maximum retries due to rate limiting."

    soup = BeautifulSoup(html_content, 'html.parser')

    stylesheets = []
    javascripts = []
    images = []
    iframes = []
    anchor_tags = []

    for link in soup.find_all('link', rel='stylesheet'):
        stylesheet_url = link.get('href')
        if stylesheet_url and 'http' in stylesheet_url:
            stylesheets.append(stylesheet_url)

    for script in soup.find_all('script', src=True):
        javascript_url = script.get('src')
        if javascript_url and 'http' in javascript_url:
            javascripts.append(javascript_url)

    for img in soup.find_all('img', src=True):
        image_url = img.get('src')
        if image_url and 'http' in image_url:
            images.append(image_url)

    for iframe in soup.find_all('iframe', src=True):
        iframe_src = iframe.get('src')
        if iframe_src and 'http' in iframe_src:
            iframes.append(iframe_src)

    for a in soup.find_all('a', href=True):
        href_url = a.get('href')
        if href_url and 'http' in href_url:
            anchor_tags.append(href_url)

    return {
        'stylesheets': stylesheets,
        'javascripts': javascripts,
        'images': images,
        'iframes': iframes,
        'anchor_tags': anchor_tags
    }, None

@app.route('/')
def home():
    return render_template('index1.html')

@socketio.on('connect')
def on_connect():
    emit('message', {'status': 'connected'})

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(message):
    if 'operation' in message:
        operation = message['operation']
        if operation == 'get_info':
            url = 'http://example.com'  # Change this to your target URL for IP info
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                ip = socket.gethostbyname(domain)
                token = '2a8fe0bdf1e60e'
                response = requests.get(f'https://ipinfo.io/{ip}?token={token}')
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        'ip': ip,
                        'isp': data.get('org'),
                        'organization': data.get('org'),
                        'asn': data.get('asn'),
                        'location': data.get('country')
                    }
                    emit('response', {'data': result})
                else:
                    emit('response', {'error': 'Failed to retrieve information'})
            except Exception as e:
                emit('response', {'error': str(e)})

        elif operation == 'get_subdomains':
            domain = 'example.com'  # Change this to your domain for subdomains
            try:
                answers = dns.resolver.resolve(domain, 'A')
                subdomains = [answer.to_text() for answer in answers]
                emit('response', {'data': subdomains})
            except dns.exception.DNSException as e:
                emit('response', {'error': str(e)})

        elif operation == 'fetch_resources':
            url = message.get('url')
            if url:
                result, error = fetch_external_resources(url)
                if error:
                    emit('response', {'error': error})
                else:
                    emit('response', {'data': result})
            else:
                emit('response', {'error': 'Missing URL'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
