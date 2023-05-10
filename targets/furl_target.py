from sys import stdin
from base64 import b64encode
import furl
import afl
afl.init()

def main():
    url_string = stdin.read()
    parsed_url = furl.furl(url_string)

    result = {}
    result["scheme"] = parsed_url.scheme
    result["host"] = parsed_url.host
    result["path"] = str(parsed_url.path)
    result["port"] = str(parsed_url.port)
    result["query"] = str(parsed_url.query)
    result["userinfo"] = parsed_url.username + ((':' + parsed_url.password) if parsed_url.password is not None else "")
    result["fragment"] = str(parsed_url.fragment)

    print("{" + ",".join(f"\"{k}\":\"{b64encode(result[k].encode('utf-8')).decode('ascii') if result[k] is not None else ''}\"" for k, v in result.items()) + "}")

if __name__ == "__main__":
    main()
