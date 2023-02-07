import sys
import rfc3987
import afl
afl.init()

def main():
    url_string = sys.stdin.read()
    parsed_url = rfc3987.parse(url_string)

    scheme = parsed_url["scheme"]
    path = parsed_url["path"]
    query = parsed_url["query"]
    fragment = parsed_url["fragment"]
    
    auth = parsed_url["authority"]
    if ":" in auth:
        port = auth[auth.rfind(":") + 1:]
        auth = auth[:-len(port) - 1]
    else:
        port = None
    
    if "@" in auth:
        username = auth[:auth.index("@")]
        auth = auth[len(username) + 1:]
    else:
        username = None

    host = auth
    
    print(f"Scheme:   {scheme if scheme else '(nil)'}")
    print(f"Host:     {host if host else '(nil)'}")
    print(f"Path:     {path if path else '(nil)'}")
    print(f"Port:     {port if port not in (b'', '', None) else '(nil)'}")
    print(f"Query:    {query if query else '(nil)'}")
    print(f"Username: {username if username else '(nil)'}")
    print(f"Fragment: {fragment if fragment else '(nil)'}")

if __name__ == "__main__":
    main()
