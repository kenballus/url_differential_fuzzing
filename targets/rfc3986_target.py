import sys
import rfc3986
import afl
afl.init()

def main():
    url_string = sys.stdin.read()
    parsed_url = rfc3986.urlparse(url_string)

    scheme = parsed_url.scheme
    host = parsed_url.host
    path = parsed_url.path
    port = parsed_url.port
    query = parsed_url.query
    username = parsed_url.userinfo
    fragment = parsed_url.fragment

    print(f"Scheme:   {scheme if scheme else '(nil)'}");
    print(f"Host:     {host if host else '(nil)'}");
    print(f"Path:     {path if path else '(nil)'}");
    print(f"Port:     {port if port else '(nil)'}");
    print(f"Query:    {query if query else '(nil)'}");
    print(f"Username: {username if username else '(nil)'}");
    print(f"Fragment: {fragment if fragment else '(nil)'}");

if __name__ == "__main__":
    main()
