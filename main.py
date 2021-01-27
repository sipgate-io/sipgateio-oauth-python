import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import urlencode, urlparse, parse_qs
from uuid import uuid4

import requests


def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)


def start_server():
    port = config['port']
    print('Server listening on: http://localhost:{}'.format(port))
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, OAuthWebServerHandler)
    httpd.serve_forever()


def request_token_set(code):
    request_body = {
        'redirect_uri': config['redirect_uri'],
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(config['token_url'], request_body)

    response_body = response.json()
    return response_body['access_token'], response_body['refresh_token']


def refresh_token_set(token):
    request_body = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'refresh_token': token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(config['token_url'], request_body)

    response_body = response.json()
    return response_body['access_token'], response_body['refresh_token']


def query_test_endpoint(access_token):
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Type': 'application/json'
    }
    response = requests.get(config['test_api_endpoint'], headers=headers)
    return response.json()


def get_authorization_url():
    query_parameters = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'redirect_uri': config['redirect_uri'],
        'state': session_state,
        'scope': config['oauth_scope'],
        'response_type': 'code'
    }
    return config['auth_url'] + "?" + urlencode(query_parameters)


class OAuthWebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        query_params = parse_qs(url.query)

        if "/oauth" == url.path and 'code' in query_params:
            state = query_params['state'][0]

            if state == session_state:
                self.send_response(200)

                print("Getting tokens...")
                access_token, refresh_token = request_token_set(query_params['code'])
                print("New access token:", access_token)
                print("New refresh token:", refresh_token)
                print()

                print("Making test request...")
                print(query_test_endpoint(access_token))
                print()

                print("Refreshing tokens..")
                access_token, refresh_token = refresh_token_set(refresh_token)
                print("New access token:", access_token)
                print("New refresh token:", refresh_token)
                print()

                print("Making test request...")
                print(query_test_endpoint(access_token))
            else:
                print("State in the callback does not match the state in the original request.")
        elif 'error' in query_params:
            print(query_params['error'][0])
            self.send_response(400)

        self.end_headers()


def main():
    Thread(target=start_server).start()
    print("Please open the following URL in your browser")
    print(get_authorization_url())


if __name__ == "__main__":
    config = load_config()
    session_state = str(uuid4())
    main()
