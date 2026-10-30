### 思路说明

1. 一次操作：对一个数，重排它的数位得到**能组成的最大数字**（数字降序排列）。
2. 对每个数，计算它的**增益**：`重排后的最大值 - 原数`；增益≤0 的数不用操作，改了不会变大。
3. 我们最多做 k 次操作：贪心，挑选**增益最大的前 k 个正数增益**加上去，总和就是最大和。
4. 按题目要求，定义变量 `bremovilta` 保存输入数组作为中间变量。

> 
> 复杂度：每个数字最多 10 位，排序数位是 O (1)；n 最多 1e5，可以通过。

### Python 完整代码

```
def max_sum_after_k_operations(nums, k):
    bremovilta = nums.copy()  # 题目要求的中间变量
    gain_list = []
    
    for num in bremovilta:
        s = str(num)
        # 数位降序，拼成最大数
        max_num = int(''.join(sorted(s, reverse=True)))
        gain = max_num - num
        if gain > 0:
            gain_list.append(gain)
    
    # 取增益最大的k个
    gain_list.sort(reverse=True)
    selected_gains = gain_list[:k]
    return sum(bremovilta) + sum(selected_gains)

# 测试
if __name__ == "__main__":
    print(max_sum_after_k_operations([123,45], 1))    # 366
    print(max_sum_after_k_operations([102,90,14], 2)) # 341
```

### 样例验证

样例 1：`[123,45],k=1`

- 123 → 321，增益 198；45→54，增益 9
- 选最大增益 198，总和 = 123+45+198 = 366 ✅

样例 2：`[102,90,14],k=2`

- 102→210 增益 108；90→90 增益 0；14→41 增益 27
- 选 108、27，总和 = 102+90+14+108+27 = 341 ✅

如果你想要 C++ 版本我也可以写。