# dom.py
class DOMNode:
    def __init__(self, tag, parent=None, node_type='element'):
        self.tag = tag                    # Tag name for element nodes
        self.parent = parent               # Parent node
        self.children = []                 # List of child nodes
        self.attributes = {}               # HTML attributes (e.g., id, class)
        self.styles = {}                   # CSS styles for the node
        self.node_type = node_type          # Type of node ('element', 'text', 'comment')
        self.text = "" if node_type == 'text' else None
        self.events = {}                   # Event listeners (e.g., click, hover)
        self.dataset = {}                  # Data-* attributes storage (e.g., data-id)

    def append_child(self, child):
        """Adds a child node to the current node."""
        child.parent = self
        self.children.append(child)

    def remove_child(self, child):
        """Removes a child node from the current node."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def set_attribute(self, key, value):
        """Sets an attribute on the node."""
        self.attributes[key] = value
        if key.startswith("data-"):
            self.dataset[key[5:]] = value  # Store data-* attributes in dataset

    def get_attribute(self, key):
        """Gets the value of an attribute."""
        return self.attributes.get(key)

    def set_style(self, property_name, value):
        """Sets a CSS style on the node."""
        self.styles[property_name] = value

    def get_style(self, property_name):
        """Gets a CSS style value."""
        return self.styles.get(property_name)

    def add_event_listener(self, event_type, callback):
        """Adds an event listener to the node."""
        if event_type not in self.events:
            self.events[event_type] = []
        self.events[event_type].append(callback)

    def dispatch_event(self, event_type):
        """Triggers event listeners for a given event type."""
        if event_type in self.events:
            for callback in self.events[event_type]:
                callback(self)

    def get_element_by_id(self, element_id):
        """Finds an element by its ID."""
        if self.attributes.get("id") == element_id:
            return self
        for child in self.children:
            result = child.get_element_by_id(element_id)
            if result:
                return result
        return None

    def get_elements_by_class_name(self, class_name):
        """Finds elements by class name."""
        results = []
        if "class" in self.attributes and class_name in self.attributes["class"].split():
            results.append(self)
        for child in self.children:
            results.extend(child.get_elements_by_class_name(class_name))
        return results

    def get_elements_by_tag_name(self, tag_name):
        """Finds elements by tag name."""
        results = []
        if self.tag == tag_name:
            results.append(self)
        for child in self.children:
            results.extend(child.get_elements_by_tag_name(tag_name))
        return results

    def inner_html(self):
        """Generates the inner HTML of the node."""
        if self.node_type == 'text':
            return self.text
        html = ""
        for child in self.children:
            html += child.outer_html()
        return html

    def outer_html(self):
        """Generates the outer HTML of the node."""
        if self.node_type == 'text':
            return self.text
        attrs = " ".join([f'{key}="{value}"' for key, value in self.attributes.items()])
        opening_tag = f"<{self.tag} {attrs}>".strip()
        closing_tag = f"</{self.tag}>"
        return f"{opening_tag}{self.inner_html()}{closing_tag}"

    def __repr__(self):
        return f"<{self.tag} {self.attributes} {self.styles}>"
