#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <curl/curl.h>

struct buffer {
    char *data;
    size_t len;
};

static size_t write_cb(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct buffer *mem = (struct buffer *)userp;

    char *ptr = realloc(mem->data, mem->len + realsize + 1);
    if (!ptr) return 0;

    mem->data = ptr;
    memcpy(&(mem->data[mem->len]), contents, realsize);
    mem->len += realsize;
    mem->data[mem->len] = '\0';
    return realsize;
}

int fetch_page(const char *url, struct buffer *out) {
    CURL *curl = curl_easy_init();
    if (!curl) return -1;

    out->data = NULL;
    out->len = 0;

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)out);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);

    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);

    return (res == CURLE_OK) ? 0 : -1;
}

// Very crude helpers: search for "temp" and "rh" lines in the HTML
void parse_and_print(const char *html) {
    const char *t = strstr(html, "temp");
    const char *h = strstr(html, "rh");
    if (!t || !h) {
        printf("Could not find temp/rh fields\n");
        return;
    }

    // Just grab some context around them (for debugging)
    char tbuf[80] = {0};
    char hbuf[80] = {0};
    snprintf(tbuf, sizeof(tbuf), "%.70s", t);
    snprintf(hbuf, sizeof(hbuf), "%.70s", h);

    printf("Raw temp context: %s\n", tbuf);
    printf("Raw rh   context: %s\n", hbuf);
}

int main(void) {
    const char *url = "http://192.168.1.44/nodeconfig.html?node=1";

    if (curl_global_init(CURL_GLOBAL_DEFAULT) != 0) {
        fprintf(stderr, "curl_global_init failed\n");
        return 1;
    }

    while (1) {
        struct buffer buf;
        if (fetch_page(url, &buf) == 0 && buf.data) {
            parse_and_print(buf.data);
            free(buf.data);
        } else {
            fprintf(stderr, "Failed to fetch page\n");
        }

        sleep(5); // poll every 5 seconds
    }

    curl_global_cleanup();
    return 0;
}
