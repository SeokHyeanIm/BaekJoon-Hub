#include <iostream>
int main()
{
    int a{}, b{};
    std::cin >> a >> b;
    std::cout << a + b << std::endl;
    std::cout << a - b << std::endl;
    std::cout << a * b << std::endl;
    std::cout << a / b << std::endl;  // 정수 나눗셈 = 몫
    std::cout << a % b << std::endl;  // 나머지
    return 0;
}