#include <iostream>
#include <algorithm>

int main()
{
    int N, K;
    std::cin >> N >> K;

    int* dp = new int[K + 1] {};

    for (int i = 0; i < N; i++)
    {
        int w, v;
        std::cin >> w >> v;

        for (int j = K; j >= w; j--)
        {
            dp[j] = std::max(dp[j], dp[j - w] + v);
        }
    }

    std::cout << dp[K];

    delete[] dp;
    return 0;
}