import requests

url = 'http://<IP>/echelon_rtb.php'
myobj = {'somekey': 'somevalue'}

x = requests.post(url, json = myobj)

print(x.text)