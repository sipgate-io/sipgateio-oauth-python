<img src="https://www.sipgatedesign.com/wp-content/uploads/wort-bildmarke_positiv_2x.jpg" alt="sipgate logo" title="sipgate" align="right" height="112" width="200"/>

# sipgate.io Python OAuth example
To demonstrate how to authenticate against the sipgate REST API using the OAuth mechanism, 
we make use of the `/account` endpoint which provides information about the account. 

> For further information regarding the sipgate REST API please visit https://api.sipgate.com/v2/doc

For educational purposes we do not use an OAuth client library in this example, but if you plan to implement authentication using OAuth in you application we recommend using one. You can find various client libraries here: [https://oauth.net/code/](https://oauth.net/code/).


## What is OAuth and when to use it
OAuth is a standard protocol for authorization. You can find more information on the OAuth website [https://oauth.net/](https://oauth.net/) or on wikipedia [https://en.wikipedia.org/wiki/OAuth](https://en.wikipedia.org/wiki/OAuth).

Applications that use the sipgate REST API on behalf of another user should use the OAuth authentication method instead of Basic Auth.


## Setup OAuth with sipgate
In order to authenticate against the sipgate REST API via OAuth you first need to create a Client in the sipgate Web App.

You can create a client as follows:

1. Navigate to [console.sipgate.com](https://console.sipgate.com/) and login with your sipgate account credentials.
2. Make sure you are in the **Clients** tab in the left side menu
3. Click the **New client** button
4. Fill out the **New client** dialog (Find information about the Privacy Policy URL and Terms of Use URL [here](#privacy-policy-url-and-terms-of-use-url))
5. The **Clients** list should contain your new client
6. Select your client
7. The entries **Id** and **Secret** are `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` required for the configuration of your application (see [Configuration](#configuration))
8. Now you just have to add your `REDIRECT_URI` to your Client by clicking the **Add redirect uri** button and fill in the dialog. In our example we provide a server within the application itself so we use `http://localhost:{port}/oauth` (the default port is `8080`). 

Now your Client is ready to use.


### Privacy Policy URL and Terms of Use URL
In the Privacy Policy URL and Terms of Use URL you must supply in the **New client** dialog when creating a new Client to use with OAuth you must supply the Privacy Policy URL and Terms of Use URL of the Service you want to use OAuth authorization for. During development and testing you can provide any valid URL but later you must change them.


## Configuration
In the [.env](./.env) file located in the project root directory insert `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` obtained in Step 7 above:

```json
...
CLIENT_ID="YOUR_CLIENT_ID"
CLIENT_SECRET="YOUR_CLIENT_SECRET"
...
```

The `OAUTH_SCOPE` defines what kind of access your Client should have to your account and is specific to your respective application. In this case, since we only want to get your basic account information as an example, the scope `account:read` is sufficient.

```
OAUTH_SCOPE=account:read
```
> Visit https://developer.sipgate.io/rest-api/oauth2-scopes/ to see all available scopes

The `REDIRECT_URI` which we have previously used in the creation of our Client is supplied to the sipgate login page to specify where you want to be redirected after successful login. As explained above, our application provides a small web server itself that handles HTTP requests directed at `http://localhost:8080/oauth`. In case there is already a service listening on port `8080` of your machine you can choose a different port number, but be sure to adjust both the `REDIRECT_URI` and the `PORT` property accordingly.

```json
...
REDIRECT_URI="http://localhost:8080/oauth",
PORT=8080,
...
```


## Prerequisites
+ python3
+ pip3


## Install dependencies
Navigate to the project's root directory.

Install dependencies:
```bash
$ pip3 install -r requirements.txt
```


## Execution
Run the application:
```bash
$ python3 main.py
```


## How It Works
In the [main.py](./main.py) we first load the configuration file [.env](./.env).
```python
load_dotenv()
```

We then generate a unique identifier `session_state` for our authorization process so that we can match a server response to our request later.
```python
session_state = str(uuid4())
```

In our main function we start a new Thread for the web server and compose the authorization URI using the properties previously loaded from the configuration file and print it to the console.
```python
def main():
    Thread(target=start_server).start()
    print("Please open the following URL in your browser")
    print(get_authorization_url())
```


Opening the link in your browser takes you to the sipgate login page where you need to confirm the scope that your Client is requesting access to before logging in with your sipgate credentials. You are then redirected to `http://localhost:8080/oauth` and our application's web server receives your request.

We use the `http.server` python module to create our web server. The `do_GET` method of the `OAuthWebServerHandler` handles our incoming get requests. 

**Note:** The `http.server` module is not recommended for production. It only implements basic security checks.
```python
class OAuthWebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        query_params = parse_qs(url.query)

        if "/oauth" == url.path and 'code' in query_params:
            state = query_params['state'][0]

            if state == session_state:
                self.send_response(200)

                access_token, refresh_token = request_token_set(query_params['code'])
                
                print(query_test_endpoint(access_token))
                
                access_token, refresh_token = refresh_token_set(refresh_token)
                
                print(query_test_endpoint(access_token))
            else:
                print("State in the callback does not match the state in the original request.")
        elif 'error' in query_params:
            print(query_params['error'][0])
            self.send_response(400)

        self.end_headers()
```

In the `do_GET` method we extract the query parameters from the url and ensure that the pathname of the requested url matches `/oauth`. After that we verify that the state transmitted by the authorization server matches the one initially supplied. In the case of multiple concurrent authorization processes this state also serves to match pairs of request and response.

We use the code obtained from the request to fetch a set of tokens from the authorization server and try them out by making an request to the `/account` endpoint of the REST API. Lastly, we use the refresh token to obtain another set of tokens. Note that this invalidates the previous set.

The `request_token_set` function fetches the tokens from the authorization server.
```python
def request_token_set(code):
    request_body = {
        'redirect_uri': os.environ.get("REDIRECT_URI"),
        'client_id': os.environ.get("CLIENT_ID"),
        'client_secret': os.environ.get("CLIENT_SECRET"),
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(os.environ.get("TOKEN_URL"), request_body)

    response_body = response.json()
    return response_body['access_token'], response_body['refresh_token']
```
We use requests to send a POST-Request to the authorization server to obtain a set of tokens (Access-Token and Refresh-Token). The POST-Request must contain the `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, `code` and `grant_type` as form data.

The `refresh_token_set` function is very similar to the `request_token_set` function. It differs in that we set the `grant_type` to `refresh_token` to indicate that we want to refresh our token, and provide the `refresh_token_set` we got from the `request_token_set` function instead of the `code`.
> ```python
> ...
> 'refresh_token': token,
> 'grant_type': 'refresh_token'
> ...
> ```

To see if authorization with the token works, we query the `/account` endpoint of the REST API.
```python
def query_test_endpoint(access_token):
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Type': 'application/json'
    }
    response = requests.get(os.environ.get("TEST_API_ENDPOINT"), headers=headers)
    return response.json()
```
To use the token for authorization we set the `Authorization` header to `Bearer` followed by a space and the `access_token` we obtained with the `request_token_set` or `refresh_token_set` function.


## Common Issues

### "State in the callback does not match the state in the original request"
Possible reasons are:
- the application was restarted and you used old url again or refreshed the browser tab


### "OSError: [Errno 98] Address already in use"
Possible reasons are:
- another instance of the application is running
- the port configured in the [.env](./.env) file is used by another application


### "PermissionError: [Errno 13] Permission denied"
Possible reasons are:
- you do not have the permission to bind to the specified port. This can happen if you use port 80, 443 or another well-known port which you can only bind to if you run the application with superuser privileges


### "invalid parameter: redirect_uri"
Possible reasons are:
- the REDIRECT_URI in the [.env](./.env) is invalid or not set
- the REDIRECT_URI is not correctly configured the sipgate Web App (You can find more information about the configuration process in the [Setup OAuth with sipgate](#setup-oauth-with-sipgate) section)


### "client not found" or "invalid client_secret"
Possible reasons are:
- the CLIENT_ID or CLIENT_SECRET configured in the [.env](./.env) is invalid. You can check them in the sipgate Web App. See [Setup OAuth with sipgate](#setup-oauth-with-sipgate)


## Related

+ [requests documentation](http://docs.python-requests.org/en/master/)
+ [http.server documentation](https://docs.python.org/3/library/http.server.html)


## Contact Us
Please let us know how we can improve this example. 
If you have a specific feature request or found a bug, please use **Issues** or fork this repository and send a **pull request** with your improvements.


## License
This project is licensed under **The Unlicense** (see [LICENSE file](./LICENSE)).


## External Libraries
This code uses the following external libraries

+ requests:
  + Licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
  + Website: http://docs.python-requests.org/en/master/
+ python-dotenv:
  + Website: https://pypi.org/project/python-dotenv/


----
[sipgate.io](https://www.sipgate.io) | [@sipgateio](https://twitter.com/sipgateio) | [API-doc](https://api.sipgate.com/v2/doc)
