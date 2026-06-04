import sys
import re
import ipaddress


# ── 域名合法性校验 ──
DOMAIN_RE = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
)


def is_valid_ip(s: str) -> bool:
    """检查是否为合法 IPv4 或 IPv6 地址"""
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def parse_line(line: str) -> tuple[str, str] | None:
    """
    解析一行，返回 (类型, 值)：
      - ('domain', 'ads.example.com')
      - ('ip', '212.117.186.252')
      - None（无效行）
    """
    line = line.strip().lower()
    if not line or line.startswith('#') or line.startswith('!'):
        return None

    # 去除末尾的点和可能的通配符
    cleaned = line.strip('*|.').rstrip('.')

    # 先检查是否为 IP 地址
    if is_valid_ip(cleaned):
        return ('ip', cleaned)

    # 再检查是否为合法域名
    if DOMAIN_RE.match(cleaned):
        return ('domain', cleaned)

    return None


def minimize_domains(file_paths: list[str], output_path: str):
    domains = set()
    ips = set()
    source_stats = {}

    # ── 1. 读取所有输入文件 ──
    for path in file_paths:
        d_count = 0
        ip_count = 0
        skipped = 0
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    result = parse_line(line)
                    if result is None:
                        skipped += 1
                        continue
                    typ, val = result
                    if typ == 'domain':
                        domains.add(val)
                        d_count += 1
                    else:
                        ips.add(val)
                        ip_count += 1
            source_stats[path] = (d_count, ip_count, skipped)
        except FileNotFoundError:
            print(f"⚠️  Warning: File not found: {path}")

    # ── 打印统计 ──
    print("📊 Source statistics:")
    for path, (d, ip, s) in source_stats.items():
        print(f"   {path}: {d:,} domains, {ip:,} IPs, {s:,} skipped")

    total_unique = len(domains) + len(ips)
    print(f"\n📦 Unique domains: {len(domains):,}  |  Unique IPs: {len(ips):,}  |  Total: {total_unique:,}")

    # ── 2. 子域名去冗余（仅域名） ──
    reversed_domains = sorted(d[::-1] for d in domains)

    minimized_reversed = []
    prev = None
    for rev_d in reversed_domains:
        if prev is not None and rev_d.startswith(prev + '.'):
            continue  # 子域名，跳过
        minimized_reversed.append(rev_d)
        prev = rev_d

    final_domains = sorted(d[::-1] for d in minimized_reversed)
    final_ips = sorted(ips)

    removed = len(domains) - len(final_domains)
    pct = (removed / len(domains) * 100) if domains else 0
    print(f"✅ Minimized domains: {len(final_domains):,} (removed {removed:,} subdomains, {pct:.1f}%)")
    print(f"✅ IPs kept: {len(final_ips):,}")
    print(f"📝 Final output: {len(final_domains) + len(final_ips):,} lines\n")

    # ── 3. 写入输出文件 ──
    # 注意：文件头不含时间戳，避免 git diff 每次都检测到变化
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Merged & Minimized Adblock List\n")
        f.write(f"# Domains: {len(final_domains):,} (removed {removed:,} subdomains)\n")
        f.write(f"# IPs: {len(final_ips):,}\n")
        f.write(f"# Total: {len(final_domains) + len(final_ips):,}\n")
        for d in final_domains:
            f.write(d + '\n')
        for ip in final_ips:
            f.write(ip + '\n')


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python minimize.py <output_file> <input_file1> [input_file2] ...")
        sys.exit(1)

    out_file = sys.argv[1]
    in_files = sys.argv[2:]
    minimize_domains(in_files, out_file)
