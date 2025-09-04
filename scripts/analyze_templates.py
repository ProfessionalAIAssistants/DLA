import os
import re

# Get all template files
template_dir = "web/templates"
templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]

# Read crm_app.py to find all render_template calls
with open('crm_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all render_template calls
referenced_templates = set()
pattern = r'render_template\([\'"]([^\'"]+\.html)[\'"]'
matches = re.findall(pattern, content)
referenced_templates.update(matches)

print("📋 Template Analysis")
print("=" * 50)

print(f"\n📁 Total templates found: {len(templates)}")
print(f"🔗 Templates referenced in code: {len(referenced_templates)}")

print("\n✅ Referenced templates:")
for template in sorted(referenced_templates):
    if template in templates:
        print(f"  ✅ {template}")
    else:
        print(f"  ❌ {template} (MISSING!)")

print("\n❓ Potentially unused templates:")
unused = set(templates) - referenced_templates
for template in sorted(unused):
    print(f"  🔍 {template}")

print("\n📊 Summary:")
print(f"  - Active templates: {len(referenced_templates)}")
print(f"  - Potentially unused: {len(unused)}")
if len(referenced_templates - set(templates)) > 0:
    print(f"  - Missing templates: {len(referenced_templates - set(templates))}")
