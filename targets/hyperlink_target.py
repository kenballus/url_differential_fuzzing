import sys
import hyperlink
import afl
afl.init()

def main():
    url_string = sys.stdin.read()
    parsed_url = hyperlink.URL.from_text(url_string)

    scheme = parsed_url.scheme
    host = parsed_url.host
    path = "/".join(parsed_url.path)
    if parsed_url.rooted:
        path = "/" + path
    port = parsed_url.port
    query = "&".join(p[0] + "=" + p[1] for p in parsed_url.query)
    userinfo = parsed_url.user
    fragment = parsed_url.fragment

    print(f"Scheme:   {scheme if scheme else '(nil)'}")
    print(f"Userinfo: {userinfo if userinfo else '(nil)'}")
    print(f"Host:     {host if host else '(nil)'}")
    print(f"Port:     {port if port not in (b'', '', None) else '(nil)'}")
    print(f"Path:     {path if path else '(nil)'}")
    print(f"Query:    {query if query else '(nil)'}")
    print(f"Fragment: {fragment if fragment else '(nil)'}")

if __name__ == "__main__":
    main()
