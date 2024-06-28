from flask import Flask, request, render_template
import requests
import socket
import dns.resolver
from urllib.parse import urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

def fetch_external_resources(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.text
        else:
            return None, f"Failed to fetch URL. Status code: {response.status_code}"

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

    except Exception as e:
        return None, str(e)

@app.route('/')
def home():
    return render_template('index.html', result=None, error=None, resources=None, subdomains=None)

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form['url']
    if not url.startswith('http'):
        url = 'http://' + url

    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        ip = socket.gethostbyname(domain)
        
        token = '2a8fe0bdf1e60e'
        response = requests.get(f'https://ipinfo.io/{ip}?token={token}')
        
        if response.status_code == 200:
            data = response.json()
            result = {
                'domain': domain,
                'server_ip': ip,
                'location': data.get('country'),
                'asn': data.get('org'),
                'isp': data.get('org'),
                'organization': data.get('org')
            }

            return render_template('index.html', result=result, error=None, resources=None, subdomains=None)
        else:
            return render_template('index.html', result=None, error='Failed to retrieve information', resources=None, subdomains=None)
    except Exception as e:
        return render_template('index.html', result=None, error=str(e), resources=None, subdomains=None)    

@app.route('/analyze_subdomains', methods=['POST'])
def analyze_subdomains():
    domain = request.form['domain']
    try:
        answers = dns.resolver.resolve(domain, 'A')
        subdomains = [answer.to_text() for answer in answers]
        return render_template('index.html', subdomains=subdomains, error=None, result=None, resources=None)
    except dns.exception.DNSException as e:
        error_message = f"Error: {str(e)}"
        return render_template('index.html', subdomains=None, error=error_message, result=None, resources=None)

@app.route('/fetch_resources', methods=['POST'])
def fetch_resources():
    url = request.form['resource_url']
    if not url.startswith('http'):
        url = 'http://' + url

    resources, error = fetch_external_resources(url)
    if error:
        return render_template('index.html', result=None, error=error, resources=None, subdomains=None)
    else:
        return render_template('index.html', result=None, error=None, resources=resources, subdomains=None)

if __name__ == '__main__':
    app.run(debug=True)
