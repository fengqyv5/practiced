import sys
import re
import ipaddress


# ── 域名合法性校验 ──
DOMAIN_RE = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
)


def is_valid_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def parse_line(line: str) -> tuple[str, str] | None:
    line = line.strip().lower()
    if not line or line.startswith('#') or line.startswith('!'):
        return None

    cleaned = line.strip('*|.').rstrip('.')

    if is_valid_ip(cleaned):
        return ('ip', cleaned)

    if DOMAIN_RE.match(cleaned):
        return ('domain', cleaned)

    return None


def minimize_domains(file_paths: list[str], output_path: str, report_path: str = None):
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

    print("📊 Source statistics:")
    for path, (d, ip, s) in source_stats.items():
        print(f"   {path}: {d:,} domains, {ip:,} IPs, {s:,} skipped")

    print(f"\n📦 Unique domains: {len(domains):,}  |  Unique IPs: {len(ips):,}")

    # ── 2. 子域名去冗余（仅域名） ──
    reversed_domains = sorted(d[::-1] for d in domains)

    minimized_reversed = []
    removed_details = []  # 👈 新增：记录被删除的明细
    prev = None
    
    for rev_d in reversed_domains:
        if prev is not None and rev_d.startswith(prev + '.'):
            # 是子域名，跳过，并记录
            sub = rev_d[::-1]
            parent = prev[::-1]
            removed_details.append((sub, parent))
            continue
        minimized_reversed.append(rev_d)
        prev = rev_d

    final_domains = sorted(d[::-1] for d in minimized_reversed)
    final_ips = sorted(ips)

    removed = len(removed_details)
    pct = (removed / len(domains) * 100) if domains else 0
    print(f"✅ Minimized domains: {len(final_domains):,} (removed {removed:,} subdomains, {pct:.1f}%)")
    print(f"✅ IPs kept: {len(final_ips):,}")
    print(f"📝 Final output: {len(final_domains) + len(final_ips):,} lines\n")

    # ── 3. 写入输出文件 ──
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Merged & Minimized Adblock List\n")
        f.write(f"# Domains: {len(final_domains):,} (removed {removed:,} subdomains)\n")
        f.write(f"# IPs: {len(final_ips):,}\n")
        f.write(f"# Total: {len(final_domains) + len(final_ips):,}\n")
        for d in final_domains:
            f.write(d + '\n')
        for ip in final_ips:
            f.write(ip + '\n')

    # ── 4. 写入删除明细报告（可选） ──
    if report_path and removed_details:
        # 按父域名分组，方便查看
        from collections import defaultdict
        parent_map = defaultdict(list)
        for sub, parent in removed_details:
            parent_map[parent].append(sub)
            
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Removed Subdomains Report ({removed:,} total)\n")
            f.write(f"# Format: [Parent Domain] -> Removed Subdomains\n\n")
            for parent in sorted(parent_map.keys()):
                subs = parent_map[parent]
                f.write(f"[{parent}] ({len(subs)} removed)\n")
                for s in sorted(subs):
                    f.write(f"  - {s}\n")
                f.write("\n")
        print(f"📄 Removed details saved to: {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python minimize.py <output_file> <input_file1> [input_file2] ...")
        sys.exit(1)
        
    out_file = sys.argv[1]
    in_files = sys.argv[2:]
    
    # 自动生成报告文件路径，例如 rules/merged.txt -> rules/removed_report.txt
    import os
    report_file = os.path.join(os.path.dirname(out_file), "removed_report.txt")
    
    minimize_domains(in_files, out_file, report_file)
