import re

with open('reddit_clone/posts/models.py', 'r') as f:
    content = f.read()

# Add indentation to 'self.content = content' line
lines = content.split('\n')
for i in range(len(lines)):
    if 'if content is not None:' in lines[i] and i+1 < len(lines) and 'self.content = content' in lines[i+1]:
        # Found the problematic line, add indentation
        leading_spaces = len(lines[i]) - len(lines[i].lstrip())
        lines[i+1] = ' ' * (leading_spaces + 4) + lines[i+1].lstrip()

# Write the fixed content back to the file
fixed_content = '\n'.join(lines)
with open('reddit_clone/posts/models.py', 'w') as f:
    f.write(fixed_content)

print('Fixed indentation in posts/models.py')
