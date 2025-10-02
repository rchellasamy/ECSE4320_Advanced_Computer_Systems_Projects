import csv, os, matplotlib.pyplot as plt
def R(p): 
    with open(p, newline='') as f: 
        return list(csv.DictReader(f))
def F(x): 
    try: return float(x)
    except: return None
def S(p): 
    os.makedirs(os.path.dirname(p), exist_ok=True); 
    plt.tight_layout(); plt.savefig(p, dpi=150); plt.close()
