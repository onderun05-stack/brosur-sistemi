#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clean up old wizard HTML from index.html"""

def cleanup():
    # Read the file
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the start marker
    start_marker = '<!-- Broşür Master - Yeni minimalist wizard JS tarafından dinamik oluşturuluyor -->'
    end_marker = '    <!-- Ghost Assistant JS -->'

    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)

    print(f'Start position: {start_pos}')
    print(f'End position: {end_pos}')

    if start_pos > 0 and end_pos > start_pos:
        # Check what's between
        between = content[start_pos + len(start_marker):end_pos]
        print(f'Characters between markers: {len(between)}')
        
        # Count old wizard elements
        old_elements = between.count('wizard-step-content') + between.count('purpose-card')
        print(f'Old wizard elements found: {old_elements}')
        
        if old_elements > 0:
            # Remove everything between start marker and end marker
            new_content = content[:start_pos + len(start_marker)] + '\n\n' + content[end_pos:]
            
            with open('templates/index.html', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print('SUCCESS! Old wizard HTML removed.')
            
            # Verify
            with open('templates/index.html', 'r', encoding='utf-8') as f:
                verify = f.read()
            remaining = verify.count('wizard-step-content') + verify.count('purpose-card')
            print(f'Remaining old elements: {remaining}')
        else:
            print('No old wizard elements found - already clean')
    else:
        print('ERROR: Markers not found correctly')

if __name__ == '__main__':
    cleanup()



