#include <stdint.h>
#include <string.h>
#include <wget/wget.h>

#define MAX_URL_LEN (32768)
static char url_string[MAX_URL_LEN];

int main(void) {
    fgets(url_string, MAX_URL_LEN, stdin);
    wget_iri *const parsed_url = wget_iri_parse(url_string, "utf-8");
    if (parsed_url == NULL) {
        return 1;
    }

    wget_iri_scheme scheme = parsed_url->scheme;
    char *const userinfo = wget_base64_encode_alloc(parsed_url->userinfo, parsed_url->userinfo != NULL ? strlen(parsed_url->userinfo) : 0);
    char *const password = wget_base64_encode_alloc(parsed_url->password, parsed_url->password != NULL ? strlen(parsed_url->password) : 0);
    char *const host = wget_base64_encode_alloc(parsed_url->host, parsed_url->host != NULL ? strlen(parsed_url->host) : 0);
    char port_str[6];
    sprintf(port_str, "%d", parsed_url->port);
    char *const port = wget_base64_encode_alloc(port_str, strlen(port_str));
    char *const path = wget_base64_encode_alloc(parsed_url->path, parsed_url->path != NULL ? strlen(parsed_url->path) : 0);
    char *const query = wget_base64_encode_alloc(parsed_url->query, parsed_url->query != NULL ? strlen(parsed_url->query) : 0);
    char *const fragment = wget_base64_encode_alloc(parsed_url->fragment, parsed_url->fragment != NULL ? strlen(parsed_url->fragment) : 0);

    printf("{\"scheme\":\"%s\",\"userinfo\":\"%s\"", scheme == 0 ? "http" : "https", userinfo);
    if (password != NULL) {
        printf(":%s", password);
    }
    printf(",\"host\":\"%s\",\"port\":\"%s\",\"path\":\"%s\",\"query\":\"%s\",\"fragment\":\"%s\"}\n", host, port, path, query, fragment);

    free(parsed_url);
    free(userinfo);
    free(password);
    free(host);
    free(port);
    free(path);
    free(query);
    free(fragment);
}
