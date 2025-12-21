#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/12/21 19:28
# @Author  : Kevin Chang
# @File    : command_parser.py
# @Software: PyCharm
def parse_command(line: str):
    """
    解析一行命令字符串，支持：
    - 空格分隔的 token
    - 单引号和双引号包裹的参数（保留引号内内容，去除引号）
    - 转义字符：\\、\"、\'
    - 返回 (command, args_list)

    Args:
        line (str): 输入的命令行字符串

    Returns:
        tuple: (command: str, args: list[str])
               如果无命令，command 为 None，args 为空列表
    """
    if not line.strip():
        return None, []

    tokens = []
    current = []
    i = 0
    n = len(line)
    in_single_quote = False
    in_double_quote = False

    while i < n:
        c = line[i]

        # 处理转义字符（仅在非单引号内生效双引号内的转义有限）
        if c == '\\' and not in_single_quote:
            if i + 1 < n:
                next_char = line[i + 1]
                if next_char in ('\\', '"', "'"):
                    current.append(next_char)
                    i += 2
                    continue
                else:
                    # 非特殊转义字符，保留反斜杠（可选行为）
                    current.append('\\')
                    i += 1
            else:
                current.append('\\')
                i += 1
            continue

        if c == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
            continue

        if c == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
            continue

        # 空格分隔 token（不在引号内）
        if c.isspace() and not in_single_quote and not in_double_quote:
            if current:
                tokens.append(''.join(current))
                current = []
            # 跳过连续空格
            while i < n and line[i].isspace():
                i += 1
            continue

        current.append(c)
        i += 1

    # 添加最后一个 token
    if current:
        tokens.append(''.join(current))

    if not tokens:
        return None, []

    command = tokens[0]
    args = tokens[1:]
    return command, args


# ✅ 测试用例
if __name__ == "__main__":
    test_cases = [
        "auth user pass",
        "get db",
        "echo 'hello world'",
        'echo "hello world"',
        'ls -l --verbose "file name"',
        r'echo \"quoted\"',
        r"echo 'don\'t stop'",
        "  \t  clean   me  \t ",
        "",
        "single",
        "cmd -f --verbose arg",
        r'cmd "a \"nested\" quote" and \'another\'',
    ]

    for case in test_cases:
        cmd, args = parse_command(case)
        print(f"Input: {repr(case)}")
        print(f"  → cmd={repr(cmd)}, args={args}")
        print()
