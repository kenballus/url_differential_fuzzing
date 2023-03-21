#include <stdint.h>
#include <curl/curl.h>

#define MAX_URL_LEN (32768)
static char url_string[MAX_URL_LEN];

int main(void) {
    fgets(url_string, MAX_URL_LEN, stdin);

    CURLU *const parsed_url = curl_url();
    CURLUcode const rc = curl_url_set(parsed_url, CURLUPART_URL, url_string, 0);
    if (rc != CURLUE_OK) {
        return 1;
    }

    char *scheme;
    char *user;
    char *password;
    char *options;
    char *host;
    char *port;
    char *path;
    char *query;
    char *fragment;

    curl_url_get(parsed_url, CURLUPART_SCHEME, &scheme, 0);
    curl_url_get(parsed_url, CURLUPART_USER, &user, 0);
    curl_url_get(parsed_url, CURLUPART_PASSWORD, &password, 0);
    curl_url_get(parsed_url, CURLUPART_OPTIONS, &options, 0);
    curl_url_get(parsed_url, CURLUPART_HOST, &host, 0);
    curl_url_get(parsed_url, CURLUPART_PORT, &port, 0);
    curl_url_get(parsed_url, CURLUPART_PATH, &path, 0);
    curl_url_get(parsed_url, CURLUPART_QUERY, &query, 0);
    curl_url_get(parsed_url, CURLUPART_FRAGMENT, &fragment, 0);

    printf("Scheme:   %s\n", scheme);
    printf("Userinfo: %s", user);
    if (password != NULL) {
        printf(":%s", password);
    }
    puts("");
    printf("Host:     %s\n", host);
    printf("Port:     %s\n", port);
    printf("Path:     %s\n", path);
    printf("Query:    %s\n", query);
    printf("Fragment: %s\n", fragment);
}
