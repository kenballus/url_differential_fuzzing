from sys import stdin
from base64 import b64encode
import yarl
import afl
afl.init()

def main():
    url_string = stdin.read()
    parsed_url = yarl.URL(url_string)

    result = {}
    result["scheme"] = parsed_url.scheme
    result["host"] = parsed_url.host
    result["path"] = parsed_url.path
    result["port"] = str(parsed_url.explicit_port) if parsed_url.explicit_port is not None else ""
    result["query"] = parsed_url.query_string
    result["userinfo"] = (parsed_url.user if parsed_url.user is not None else "") + ((":" + parsed_url.password) if parsed_url.password is not None else "")
    result["fragment"] = parsed_url.fragment

    print("{" + ",".join(f"\"{k}\":\"{b64encode(result[k].encode('utf-8')).decode('ascii') if result[k] is not None else ''}\"" for k, v in result.items()) + "}")

if __name__ == "__main__":
    main()
