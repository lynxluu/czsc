import requests
from bs4 import BeautifulSoup
import requests
import ssl

# Create an SSL context object
ssl_context = ssl.SSLContext()

# Set the verify mode to CERT_REQUIRED
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Set the path to the CA certificate file
ssl_context.load_verify_locations('/path/to/ca_certificate_file')

# Make a request using the SSL context object
response = requests.get('https://example.com', verify=ssl_context)

url = 'http://data.eastmoney.com/hsgt/top10.html'
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')
table = soup.find_all('table')[0]
rows = table.find_all('tr')
for row in rows[1:11]:
    cols = row.find_all('td')
    print(cols[1].text)