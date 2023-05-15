#include <stdlib.h>
#include <string.h>

#include "curl/include/curl/curl.h"
#include "curl/lib/curl_base64.h"

#define MAX_URL_LEN (32768)
static char empty_string[] = "";
static size_t unused;
static char url_string[MAX_URL_LEN];

int main(void) {
    fgets(url_string, MAX_URL_LEN, stdin);

    CURLU *const parsed_url = curl_url();
    CURLUcode const rc = curl_url_set(parsed_url, CURLUPART_URL, url_string, CURLU_NON_SUPPORT_SCHEME);
    if (rc != CURLUE_OK) {
        return 1;
    }

    char *scheme = NULL;
    char *user = NULL;
    char *password = NULL;
    char *host = NULL;
    char *port = NULL;
    char *path = NULL;
    char *query = NULL;
    char *fragment = NULL;

    curl_url_get(parsed_url, CURLUPART_SCHEME, &scheme, 0);
    curl_url_get(parsed_url, CURLUPART_USER, &user, 0);
    curl_url_get(parsed_url, CURLUPART_PASSWORD, &password, 0);
    curl_url_get(parsed_url, CURLUPART_HOST, &host, 0);
    curl_url_get(parsed_url, CURLUPART_PORT, &port, 0);
    curl_url_get(parsed_url, CURLUPART_PATH, &path, 0);
    curl_url_get(parsed_url, CURLUPART_QUERY, &query, 0);
    curl_url_get(parsed_url, CURLUPART_FRAGMENT, &fragment, 0);
    // Leaving off OPTIONS and ZONEID for now.

    char *b64_scheme = NULL;
    char *b64_userinfo = NULL;
    char *b64_password = NULL;
    char *b64_host = NULL;
    char *b64_port = NULL;
    char *b64_path = NULL;
    char *b64_query = NULL;
    char *b64_fragment = NULL;

    if (scheme != NULL) {
        Curl_base64_encode(scheme, 0, &b64_scheme, &unused);
    } else {
        b64_scheme = empty_string;
    }
    if (user != NULL && password != NULL) {
        if (realloc(user, strlen(user) + strlen(password) + 1) != 0) {
            return 2;
        }
        strcat(user, password);
        Curl_base64_encode(user, 0, &b64_userinfo, &unused);
    } else if (user != NULL && password == NULL) {
        Curl_base64_encode(user, 0, &b64_userinfo, &unused);
    } else if (user == NULL && password != NULL) {
        char userinfo[] = {':', '\0'};
        if (realloc(userinfo, 1 + strlen(password) + 1) != 0) {
            return 2;
        }
        strcat(userinfo, password);
        Curl_base64_encode(userinfo, 0, &b64_userinfo, &unused);
    } else {
        b64_userinfo = empty_string;
    }
    if (password != NULL) {
        Curl_base64_encode(password, 0, &b64_password, &unused);
    } else {
        b64_password = empty_string;
    }
    if (host != NULL) {
        Curl_base64_encode(host, 0, &b64_host, &unused);
    } else {
        b64_host = empty_string;
    }
    if (port != NULL) {
        Curl_base64_encode(port, 0, &b64_port, &unused);
    } else {
        b64_port = empty_string;
    }
    if (path != NULL) {
        Curl_base64_encode(path, 0, &b64_path, &unused);
    } else {
        b64_path = empty_string;
    }
    if (query != NULL) {
        Curl_base64_encode(query, 0, &b64_query, &unused);
    } else {
        b64_query = empty_string;
    }
    if (fragment != NULL) {
        Curl_base64_encode(fragment, 0, &b64_fragment, &unused);
    } else {
        b64_fragment = empty_string;
    }

    printf("{\"scheme\":\"%s\",\"userinfo\":\"%s\",\"host\":\"%s\",\"port\":\"%s\",\"path\":\"%s\",\"query\":\"%s\",\"fragment\":\"%s\"}\n", b64_scheme, b64_userinfo, b64_host, b64_port, b64_path, b64_query, b64_fragment);
}
