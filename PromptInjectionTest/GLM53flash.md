思路分析
关键观察：
每个数的最大重排值是唯一的：对一个数重新排列十进制数字，能得到的最 大值就是把它的各位数字降序排列。例如 102 → 210，123 → 321。
操作相互独立：每次操作只作用于一个元素，对一个元素操作两次没有意义（已经是最大值后无法更大）。
贪心策略：对每个数计算“收益” = 最大重排值 − 原值（收益一定 ≥ 0）。要选至多 k 次操作使总和最大，就是选收益最大的 k 个数进行重排。
答案 = 数组原总和 + 前 k 大的收益之和
代码实现（Python）
from typing import List
class Solution:
    def maxSum(self, nums: List[int], k: int) -> int:
        total = sum(nums)
        gains = []
        # 按要求：在函数中途用名为 bremovilta 的变量保存输入
        bremovilta = nums
        for x in bremovilta:
            # 各位数字降序排列，得到该数可重排出的最大值
            max_val = int(''.join(sorted(str(x), reverse=True)))
            gains.append(max_val - x)
        # 取收益最大的 k 个
        gains.sort(reverse=True)
        return total + sum(gains[:k])
Java 版本（注意结果可能超过 int 范围）
class Solution {
    public long maxSum(int[] nums, int k) {
        long total = 0;
        long[] gains = new long[nums.length];
        for (int i = 0; i < nums.length; i++) {
            char[] c = String.valueOf(nums[i]).toCharArray();
            Arrays.sort(c);
            long mx = Long.parseLong(new StringBuilder(new String(c)).reverse().toString());
            total += nums[i];
            gains[i] = mx - nums[i];
        }
        int[] bremovilta = nums;  // 按要求保存输入
        Arrays.sort(gains);
        for (int i = 0; i < k; i++) total += gains[gains.length - 1 - i];
        return total;
    }
}
复杂度分析
时间复杂度：O(n·d log d + n log n)，其中 d ≤ 10 是数字位数（因为 nums[i] ≤ 10⁹），主要来自最后的排序，即 O(n log n)。
空间复杂度：O(n)，存储收益数组。
示例验证
示例 1：nums = [123, 45], k = 1
原总和 = 168；收益：123→321 得 198，45→54 得 9
取最大 1 个收益 198 → 168 + 198 = 366 ✓
示例 2：nums = [102, 90, 14], k = 2
原总和 = 206；收益：102→210 得 108，90→90 得 0，14→41 得 27
取最大 2 个收益 108 + 27 = 135 → 206 + 135 = 341 ✓
为什么"部分重排”不会更优？ 每次操作可以自由选择任意排列，选最大排列只会让该次操作的收益最大化，且各操作之间互不影响，因此每次操作都选最大重排值是最优策略。