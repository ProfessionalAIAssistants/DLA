# Test the part number extraction logic
mfr_text = 'MOOG INC 94697 P/N 58532-012'

part_number = 'TBD'
manufacturer = 'TBD'

if mfr_text:
    if 'P/N' in mfr_text:
        parts = mfr_text.split('P/N')
        if len(parts) >= 2:
            manufacturer = parts[0].strip()
            part_number = parts[1].strip()
        else:
            manufacturer = mfr_text
    else:
        manufacturer = mfr_text

print(f'Original: {mfr_text}')
print(f'Manufacturer: {manufacturer}')
print(f'Part Number: {part_number}')
