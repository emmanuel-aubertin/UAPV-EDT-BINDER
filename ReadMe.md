
# Get Your EDT-UAPV Token

Welcome to the EDT-UAPV token retrieval tool! 
## Prerequisites

Before you start, ensure you have the following prerequisites installed on your system:

- Python 3.x
- pip (Python package installer)

## Installation

### Step 1: Install Python Dependencies

First, you need to install the necessary Python libraries. Open your terminal and run the following command:

```bash
pip install -r requirements.txt
```

This command reads the `requirements.txt` file and installs all the listed Python packages.

### Step 2: Install WebDriver

This tool requires a WebDriver for running automated tasks in a web browser. We use ChromeDriver as an example here, but you can use any WebDriver compatible with your browser.

- **ChromeDriver:** Visit the [ChromeDriver download page](https://sites.google.com/a/chromium.org/chromedriver/) and download the version that matches your Chrome browser version. Extract the downloaded file and ensure the `chromedriver` executable is in your system's PATH.

## Usage

To use this tool, you need to send a POST request with your University of Avignon credentials. Below is an example using `curl`:

### Curl Example

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

Replace `uapvXXXXXXX` with your actual username and `YOUR_PASSWORD` with your password.

### Response

Upon successful authentication, the server will respond with a JSON object containing your name and token:

```json
{
    "name": "Aubertin Emmanuel",
    "token": "MY_TOKEN_HERE",
    "isStudent": "true",
}
```

Store this token securely, as it will be used for subsequent API requests to the University of Avignon's systems.
This can expire shortly, see it like an session token.

## Note

>> Ensure you keep your credentials secure and do not share your token with others.

