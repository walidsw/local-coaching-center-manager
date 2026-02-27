import glob, os

for filepath in glob.glob('kv/*.kv'):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace background_color with bg_color for widgets that we'll custom style
    content = content.replace('background_color:', 'bg_color:')
    
    # Also change Rectangle to RoundedRectangle with a radius for box backgrounds
    # The user wanted boxes to be curved
    # typically they have:
    # Rectangle:
    #     pos: self.pos
    #     size: self.size
    content = content.replace(
        'Rectangle:\n                    pos: self.pos\n                    size: self.size',
        'RoundedRectangle:\n                    pos: self.pos\n                    size: self.size\n                    radius: [dp(8)]'
    )
    # in case of different indentation
    content = content.replace(
        'Rectangle:\n                pos: self.pos\n                size: self.size',
        'RoundedRectangle:\n                pos: self.pos\n                size: self.size\n                radius: [dp(8)]'
    )
    
    with open(filepath, 'w') as f:
        f.write(content)

print("Updated kv files")
