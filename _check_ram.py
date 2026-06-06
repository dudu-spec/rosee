import psutil

mem = psutil.virtual_memory()
print(f"Total: {mem.total / 1024**3:.1f} GB")
print(f"Disponivel: {mem.available / 1024**3:.1f} GB")
print(f"Usado: {mem.used / 1024**3:.1f} GB ({mem.percent}%)")

print("\nProcessos usando mais RAM:")
procs = []
for p in psutil.process_iter(['name', 'memory_info']):
    try:
        rss = p.info['memory_info'].rss if p.info['memory_info'] else 0
        if rss > 50 * 1024 * 1024:  # > 50MB
            procs.append((p.info['name'], rss))
    except:
        pass
procs.sort(key=lambda x: x[1], reverse=True)
for name, rss in procs[:10]:
    print(f"  {name:25s} {rss / 1024**3:.2f} GB")
