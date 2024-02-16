# Get your edt-uapv token

## Dependencies

Install python dependecies
```bash
pip install -r requirements.txt
```
You need to install chromedriver

## Curl Example :

```bash
curl -X 'POST' \
  'http://127.0.0.1:5000/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "uapvXXXXXXX",
  "password": "YOUR_PASSWORD"
}'
```

Ouptut :

```json
{
    "name": "Aubertin Emmanuel",
    "token": "MY_TOKEN_HERE"
}
```