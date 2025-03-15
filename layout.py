# layout.py

class LayoutBox:
    def __init__(self, node, x, y, width, height):
        self.node = node
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children = []  # Store child boxes for proper nesting

    def __repr__(self):
        return (f"LayoutBox({self.node.tag}, x={self.x}, y={self.y}, "
                f"width={self.width}, height={self.height}, children={len(self.children)})")


def layout_tree(node, x, y, parent_width=800):
    """
    Recursively generates layout boxes for each node in the HTML structure.
    """
    if isinstance(node, str):
        return None  # Ignore plain text (can be handled separately)

    width = parent_width  # Allow dynamic width adjustment
    height = 20  # Default height (can be modified based on content)
    
    # Create a layout box for the current node
    box = LayoutBox(node, x, y, width, height)
    
    # Layout child elements
    child_y = y + height  # Move below the current box
    for child in node.children:
        child_box = layout_tree(child, x + 10, child_y, width - 20)  # Indent children
        if child_box:
            box.children.append(child_box)
            child_y += child_box.height  # Stack children below each other

    return box
