import sys
import furl
import afl
afl.init()

def main():
    url_string = sys.stdin.read()
    parsed_url = furl.furl(url_string)

    scheme = str(parsed_url.scheme) if parsed_url.scheme is not None else None
    host = str(parsed_url.host) if parsed_url.host is not None else None
    path = str(parsed_url.path) if parsed_url.path is not None else None
    port = parsed_url.port
    query = str(parsed_url.query) if parsed_url.query is not None else None
    userinfo = str(parsed_url.username) if parsed_url.username is not None else None
    fragment = str(parsed_url.fragment) if parsed_url.fragment is not None else None

    print(f"Scheme:   {scheme if scheme else '(nil)'}")
    print(f"Userinfo: {userinfo if userinfo else '(nil)'}")
    print(f"Host:     {host if host else '(nil)'}")
    print(f"Port:     {port if port not in (b'', '', None) else '(nil)'}")
    print(f"Path:     {path if path else '(nil)'}")
    print(f"Query:    {query if query else '(nil)'}")
    print(f"Fragment: {fragment if fragment else '(nil)'}")
if __name__ == "__main__":
    main()
