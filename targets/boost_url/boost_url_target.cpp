#include <boost/url/src.hpp>
#include <iostream>

int main() {
    std::string input;
    std::string line;
    while (std::getline(std::cin, line)) {
        input += line;
    }

    boost::urls::url const u(input);
    std::cout << "Scheme:   " << (u.scheme() != std::string() ? u.scheme() : "(nil)") << "\n";
    std::cout << "Host:     " << (u.host() != std::string() ? u.host() : "(nil)") << "\n";
    std::cout << "Path:     " << (u.path() != std::string() ? u.path() : "(nil)") << "\n";
    std::cout << "Port:     " << (u.port() != std::string() ? u.port() : "(nil)") << "\n";
    std::cout << "Query:    " << (u.query() != std::string() ? u.query() : "(nil)") << "\n";
    std::cout << "Username: " << (u.userinfo() != std::string() ? u.userinfo() : "(nil)") << "\n";
    std::cout << "Fragment: " << (u.fragment() != std::string() ? u.fragment() : "(nil)") << "\n";
}
