import sys
import furl
import afl
afl.init()

def main():
    url_string = sys.stdin.read()
    parsed_url = furl.furl(url_string)

    scheme = str(parsed_url.scheme)
    host = str(parsed_url.host)
    path = str(parsed_url.path)
    port = str(parsed_url.port)
    query = str(parsed_url.query)
    username = str(parsed_url.username) if parsed_url.username is not None else None
    fragment = str(parsed_url.fragment)

    print(f"Scheme:   {scheme if scheme else '(nil)'}");
    print(f"Host:     {host if host else '(nil)'}");
    print(f"Path:     {path if path else '(nil)'}");
    print(f"Port:     {port if port else '(nil)'}");
    print(f"Query:    {query if query else '(nil)'}");
    print(f"Username: {username if username else '(nil)'}");
    print(f"Fragment: {fragment if fragment else '(nil)'}");

if __name__ == "__main__":
    main()
