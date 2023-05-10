from sys import stdin
from base64 import b64encode
import urllib3
import afl
afl.init()

def main():
    url_string = stdin.read()
    parsed_url = urllib3.util.parse_url(url_string)

    result = {}
    result["scheme"] = parsed_url.scheme
    result["host"] = parsed_url.host
    result["path"] = parsed_url.path
    result["port"] = str(parsed_url.port) if parsed_url.port is not None else ""
    result["query"] = parsed_url.query
    result["userinfo"] = parsed_url.auth
    result["fragment"] = parsed_url.fragment

    print("{" + ",".join(f"\"{k}\":\"{b64encode(result[k].encode('utf-8')).decode('ascii') if result[k] is not None else ''}\"" for k, v in result.items()) + "}")

if __name__ == "__main__":
    main()
