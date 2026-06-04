import sys

def minimize_domains(file_paths, output_path):
    domains = set()
    
    # 1. 读取所有文件，过滤注释和空行
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # 统一转小写，去除末尾可能存在的点
                    domain = line.lower().rstrip('.')
                    if domain:
                        domains.add(domain)
        except FileNotFoundError:
            print(f"Warning: File not found: {path}")

    original_count = len(domains)
    print(f"Total unique domains before minimizing: {original_count}")

    # 2. 核心算法：反转域名并排序
    # 例如: example.com -> moc.elpmaxe
    #      ads.example.com -> moc.elpmaxe.sda
    # 排序后，父域名会紧挨着排在子域名前面
    reversed_domains = sorted([d[::-1] for d in domains])
    
    # 3. 遍历并剔除子域名
    minimized_reversed = []
    prev = None
    for rev_d in reversed_domains:
        # 如果当前域名以 "上一个域名 + ." 开头，说明它是上一个域名的子域名
        if prev is not None and rev_d.startswith(prev + '.'):
            continue
        minimized_reversed.append(rev_d)
        prev = rev_d
        
    # 4. 将结果反转回来并保存
    final_domains = [d[::-1] for d in minimized_reversed]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for d in final_domains:
            f.write(d + '\n')
            
    print(f"Final minimized domains: {len(final_domains)}")
    print(f"Removed {original_count - len(final_domains)} redundant subdomains.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python minimize.py <output_file> <input_file1> [input_file2] ...")
        sys.exit(1)
        
    out_file = sys.argv[1]
    in_files = sys.argv[2:]
    minimize_domains(in_files, out_file)
