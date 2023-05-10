from sys import stdin
from base64 import b64encode
import hyperlink
import afl
afl.init()

def main():
    url_string = stdin.read()
    parsed_url = hyperlink.URL.from_text(url_string)

    result = {}
    result["scheme"] = parsed_url.scheme
    result["host"] = parsed_url.host
    result["path"] = ("/" if parsed_url.rooted else "") + "/".join(parsed_url.path)
    result["port"] = str(parsed_url.port)
    result["query"] = "&".join(p[0] + (f"={p[1]}" if p[1] is not None else "") for p in parsed_url.query)
    result["userinfo"] = parsed_url.userinfo
    result["fragment"] = parsed_url.fragment

    print("{" + ",".join(f"\"{k}\":\"{b64encode(result[k].encode('utf-8')).decode('ascii') if result[k] is not None else ''}\"" for k, v in result.items()) + "}")

if __name__ == "__main__":
    main()
