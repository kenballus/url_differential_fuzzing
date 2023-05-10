from sys import stdin
from base64 import b64encode
import rfc3986
import afl
afl.init()

def main():
    url_string = stdin.read()
    parsed_url = rfc3986.ParseResult.from_string(url_string)

    result = {}
    result["scheme"] = parsed_url.scheme
    result["host"] = parsed_url.host
    result["path"] = parsed_url.path
    result["port"] = str(parsed_url.port)
    result["query"] = parsed_url.query
    result["userinfo"] = parsed_url.userinfo
    result["fragment"] = parsed_url.fragment

    print("{" + ",".join(f"\"{k}\":\"{b64encode(result[k].encode('utf-8')).decode('ascii') if result[k] is not None else ''}\"" for k, v in result.items()) + "}")

if __name__ == "__main__":
    main()
