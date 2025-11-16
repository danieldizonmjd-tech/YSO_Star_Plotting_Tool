import pandas as pd
import numpy as np
from pathlib import Path

def parse_paper_a(filepath):
    """Parse Paper A (apjadd25ft1_mrt.txt) - SPICY linear YSOs"""
    data = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines[39:]:
        if not line.strip() or line.startswith('---'):
            continue
        try:
            parts = line.split()
            if len(parts) < 26:
                continue
            
            spicy_id = int(parts[0])
            yso_class = parts[1]
            
            lc_class = parts[18]
            
            rah = int(parts[20])
            ram = int(parts[21])
            ras = float(parts[22])
            ra_deg = rah * 15 + ram * 15/60 + ras * 15/3600
            
            de_str = parts[23]
            de_sign = -1 if de_str.startswith('-') else 1
            ded = int(de_str.lstrip('-'))
            dem = int(parts[24])
            des = float(parts[25])
            de_deg = de_sign * (ded + dem/60 + des/3600)
            
            lc_type = 'Linear(+)' if 'linear(+)' in lc_class.lower() else 'Linear(-)' if 'linear(-)' in lc_class.lower() else 'Unknown'
            
            data.append({
                'SPICY_ID': spicy_id,
                'Objname': f'SPICY_{spicy_id}',
                'RAdeg': ra_deg,
                'DEdeg': de_deg,
                'YSO_CLASS': yso_class,
                'LCType': lc_type,
                'VarClass1': lc_class
            })
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {e}")
            continue
    
    return pd.DataFrame(data)

def parse_paper_b(filepath):
    """Parse Paper B (apjsadc397t2_mrt.txt)"""
    data = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.startswith('J') or line.startswith('L'):
            parts = line.split()
            if len(parts) >= 16:
                try:
                    data.append({
                        'Objname': parts[0],
                        'RAdeg': float(parts[1]),
                        'DEdeg': float(parts[2]),
                        'SED_SLOPE': float(parts[3]) if parts[3] != '?' else np.nan,
                        'YSO_CLASS': parts[4],
                        'Number': int(parts[5]),
                        'W2magMean': float(parts[6]),
                        'W2magMed': float(parts[7]),
                        'sig_W2Flux': float(parts[8]),
                        'err_W2Flux': float(parts[9]),
                        'delW2mag': float(parts[10]),
                        'Period': float(parts[11]),
                        'FLP_LSP_BOOT': float(parts[12]),
                        'slope': float(parts[13]),
                        'e_slope': float(parts[14]),
                        'r_value': float(parts[15]),
                        'LCType': parts[-1] if len(parts) > 21 else 'Unknown'
                    })
                except (ValueError, IndexError):
                    continue
    
    return pd.DataFrame(data)

def parse_paper_c(filepath):
    """Parse Paper C (apjsadf4e6t4_mrt.txt) - LAMOST YSO candidates"""
    data = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines[30:]:
        if not line.strip() or line.startswith('---'):
            continue
        try:
            parts = line.split()
            if len(parts) < 5:
                continue
            
            obsid = parts[0]
            design = parts[1]
            ra_deg = float(parts[2])
            de_deg = float(parts[3])
            
            data.append({
                'OBSID': obsid,
                'Objname': design,
                'RAdeg': ra_deg,
                'DEdeg': de_deg
            })
        except (ValueError, IndexError):
            continue
    
    return pd.DataFrame(data)

def main():
    output_dir = Path('/Users/marcus/Desktop/YSO/culled_csvs')
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("PHASE 2: FILTERING AND CSV GENERATION")
    print("=" * 80)
    
    file_mapping = {
        'A': '/Users/marcus/Desktop/YSO/apjadd25ft1_mrt.txt',
        'B': '/Users/marcus/Desktop/YSO/apjsadc397t2_mrt.txt',
        'C': '/Users/marcus/Desktop/YSO/apjsadf4e6t4_mrt.txt'
    }
    
    print("\n[PAPER A] Loading apjadd25ft1_mrt.txt...")
    df_a = parse_paper_a(file_mapping['A'])
    print(f"  Raw records: {len(df_a)}")
    
    df_a_filtered = df_a[df_a['DEdeg'] > -30].copy()
    print(f"  After DEdeg > -30°: {len(df_a_filtered)}")
    
    df_a_linear_plus = df_a_filtered[df_a_filtered['LCType'] == 'Linear(+)'].copy()
    df_a_linear_minus = df_a_filtered[df_a_filtered['LCType'] == 'Linear(-)'].copy()
    
    print(f"  Linear(+) sources: {len(df_a_linear_plus)}")
    print(f"  Linear(-) sources: {len(df_a_linear_minus)}")
    
    output_a_plus = str(output_dir / 'PaperA_LinearPlus.csv')
    output_a_minus = str(output_dir / 'PaperA_LinearMinus.csv')
    
    df_a_linear_plus.to_csv(output_a_plus, index=False)
    df_a_linear_minus.to_csv(output_a_minus, index=False)
    
    print(f"  ✓ Saved: PaperA_LinearPlus.csv ({len(df_a_linear_plus)} sources)")
    print(f"  ✓ Saved: PaperA_LinearMinus.csv ({len(df_a_linear_minus)} sources)")
    
    print("\n[PAPER B] Loading apjsadc397t2_mrt.txt...")
    df_b = parse_paper_b(file_mapping['B'])
    print(f"  Raw records: {len(df_b)}")
    
    df_b_filtered = df_b[df_b['DEdeg'] > -30].copy()
    print(f"  After DEdeg > -30°: {len(df_b_filtered)}")
    
    df_b_linear = df_b_filtered[df_b_filtered['LCType'] == 'Linear'].copy()
    print(f"  Linear sources: {len(df_b_linear)}")
    
    output_b_linear = str(output_dir / 'PaperB_Linear.csv')
    df_b_linear.to_csv(output_b_linear, index=False)
    print(f"  ✓ Saved: PaperB_Linear.csv ({len(df_b_linear)} sources)")
    
    print("\n[PAPER C] Loading apjsadf4e6t4_mrt.txt...")
    df_c = parse_paper_c(file_mapping['C'])
    print(f"  Raw records: {len(df_c)}")
    
    output_c_all = str(output_dir / 'PaperC_AllSources.csv')
    df_c.to_csv(output_c_all, index=False)
    print(f"  ✓ Saved: PaperC_AllSources.csv ({len(df_c)} sources)")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Output directory: {output_dir}")
    print("\nCSVs generated:")
    print(f"  • PaperA_LinearPlus.csv: {len(df_a_linear_plus)} sources")
    print(f"  • PaperA_LinearMinus.csv: {len(df_a_linear_minus)} sources")
    print(f"  • PaperB_Linear.csv: {len(df_b_linear)} sources")
    print(f"  • PaperC_AllSources.csv: {len(df_c)} sources")
    print(f"\nTotal sources for ZTF analysis: {len(df_a_linear_plus) + len(df_a_linear_minus) + len(df_b_linear) + len(df_c)}")
    
    return {
        'PaperA_LinearPlus': df_a_linear_plus,
        'PaperA_LinearMinus': df_a_linear_minus,
        'PaperB_Linear': df_b_linear,
        'PaperC_AllSources': df_c
    }

if __name__ == '__main__':
    dfs = main()
