import pandas as pd
import numpy as np
from pathlib import Path

def parse_mrt_file(filepath):
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
                        'YSO_CLASS': parts[4],
                        'W2magMean': float(parts[6]),
                        'delW2mag': float(parts[10]),
                        'LCType': parts[-1] if len(parts) > 21 else 'Unknown'
                    })
                except (ValueError, IndexError):
                    continue
    
    return pd.DataFrame(data)

def main():
    output_dir = Path('/Users/marcus/Desktop/YSO/ztf_candidates')
    output_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("PHASE 1: LOAD AND FILTER INFRARED SOURCES")
    print("="*80 + "\n")
    
    print("Loading YSO data from 3 papers...")
    dfs = []
    for file in Path('/Users/marcus/Desktop/YSO').glob('*_mrt.txt'):
        print(f"  Parsing {file.name}...")
        df = parse_mrt_file(str(file))
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal objects loaded: {len(combined_df):,}\n")
    
    combined_df = combined_df.dropna(subset=['YSO_CLASS', 'LCType'])
    print(f"After removing missing values: {len(combined_df):,}\n")
    
    print("Filtering criteria:")
    print("  1. Declination > -30° (northern sky accessible)")
    print("  2. Light curve type = Linear (smooth, predictable)")
    print("  3. Valid YSO classification\n")
    
    valid_classes = ['ClassI', 'ClassII', 'ClassIII', 'FS']
    filtered_df = combined_df[
        (combined_df['DEdeg'] > -30) &
        (combined_df['LCType'] == 'Linear') &
        (combined_df['YSO_CLASS'].isin(valid_classes))
    ].copy()
    
    print(f"After filtering: {len(filtered_df):,} sources\n")
    
    print("YSO Class Distribution:")
    for cls, count in filtered_df['YSO_CLASS'].value_counts().items():
        print(f"  {cls}: {count}")
    
    print(f"\nInfrared Brightness (WISE W2):")
    print(f"  Mean: {filtered_df['W2magMean'].mean():.2f} mag")
    print(f"  Brightest: {filtered_df['W2magMean'].min():.2f} mag")
    print(f"  Dimmest: {filtered_df['W2magMean'].max():.2f} mag")
    
    print(f"\nVariability Amplitude:")
    print(f"  Mean: {filtered_df['delW2mag'].mean():.3f} mag")
    print(f"  Range: {filtered_df['delW2mag'].min():.3f} - {filtered_df['delW2mag'].max():.2f} mag")
    
    output_file = output_dir / 'filtered_sources.csv'
    filtered_df.to_csv(output_file, index=False)
    print(f"\n✓ Saved filtered sources to: {output_file}")
    
    print(f"\nReady for ZTF optical analysis (Phase 2)")
    print("Run: python3 ztf_analysis.py")

if __name__ == '__main__':
    main()
