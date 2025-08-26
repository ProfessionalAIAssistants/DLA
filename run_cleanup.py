#!/usr/bin/env python3
"""
File Cleanup Script - Remove temporary diagnostic files
"""

import os
import glob

def cleanup_files():
    """Remove temporary files safely"""
    
    # Define patterns of files to remove
    cleanup_patterns = [
        'check_*.py',
        'cleanup_*.py', 
        'debug_*.py',
        'fix_*.py',
        'optimize_*.py',
        'update_*.py',
        'validate_*.py',
        'verify_*.py',
        'analyze_*.py',
        'compare_*.py',
        'final_*.py',
        'simple_*.py',
        'quick_*.py',
        'demo_*.py',
        'direct_*.py',
        'full_*.py',
        'implement_*.py',
        'test_*.py',
        'add_*.py',
        'create_*.py',
        'copy_*.py'
    ]
    
    # Individual files to remove
    individual_files = [
        'workflow_analysis.py',
        'smart_copy_data.py',
        'diagnostic_output.txt',
        'diagnostic_results.json',
        'database_status.json'
    ]
    
    removed_files = []
    errors = []
    
    # Remove files matching patterns
    for pattern in cleanup_patterns:
        try:
            files = glob.glob(pattern)
            for file in files:
                if os.path.exists(file):
                    os.remove(file)
                    removed_files.append(file)
                    print(f"✅ Removed: {file}")
        except Exception as e:
            errors.append(f"Error with pattern {pattern}: {e}")
    
    # Remove individual files
    for file in individual_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                removed_files.append(file)
                print(f"✅ Removed: {file}")
        except Exception as e:
            errors.append(f"Error removing {file}: {e}")
    
    print(f"\n🎉 CLEANUP COMPLETE!")
    print(f"   Files removed: {len(removed_files)}")
    if errors:
        print(f"   Errors: {len(errors)}")
        for error in errors:
            print(f"   ❌ {error}")
    
    return removed_files, errors

if __name__ == "__main__":
    print("🧹 Starting file cleanup...")
    removed, errors = cleanup_files()
    
    if not errors:
        print("\n✅ All temporary files removed successfully!")
    else:
        print(f"\n⚠️  Cleanup completed with {len(errors)} errors")
