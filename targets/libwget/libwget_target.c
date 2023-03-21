#include <stdint.h>
#include <wget/wget.h>

#define MAX_URL_LEN (32768)
static char url_string[MAX_URL_LEN];

int main(void) {
    fgets(url_string, MAX_URL_LEN, stdin);
    wget_iri const *const parsed_url = wget_iri_parse(url_string, "utf-8");
    if (parsed_url == NULL) {
        return 1;
    }

    wget_iri_scheme scheme = parsed_url->scheme;
    char const *const userinfo = parsed_url->userinfo;
    char const *const password = parsed_url->password;
    char const *const host = parsed_url->host;
    uint16_t const port = parsed_url->port;
    char const *const path = parsed_url->path;
    char const *const query = parsed_url->query;
    char const *const fragment = parsed_url->fragment;

    printf("Scheme:   %s\n", scheme == 0 ? "http" : "https");
    printf("Userinfo: %s", userinfo);
    if (password != NULL) {
        printf(":%s", password);
    }
    puts("");
    printf("Host:     %s\n", host);
    printf("Port:     %d\n", port);
    printf("Path:     %s\n", path);
    printf("Query:    %s\n", query);
    printf("Fragment: %s\n", fragment);
}
