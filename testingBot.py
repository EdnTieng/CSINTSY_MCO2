import re

class SimpleFamilyChatbot:
    def __init__(self):
        # parent[child] = set of parents
        self.parent = {}  # child -> set of parents
        # gender[name] = 'male' or 'female'
        self.gender = {}

    def add_parent(self, parent, child):
        if parent == child:
            return "That's impossible!"
        # Check for cycles
        if self.would_create_cycle(parent, child):
            return "That's impossible!"
        self.parent.setdefault(child, set()).add(parent)
        return "OK! I learned something."

    def would_create_cycle(self, parent, child):
        # Check if parent is already a descendant of child
        visited = set()
        
        def is_descendant(ancestor, descendant):
            if ancestor == descendant:
                return True
            if descendant in visited:
                return False
            visited.add(descendant)
            
            for p in self.parent.get(descendant, set()):
                if is_descendant(ancestor, p):
                    return True
            return False
        
        return is_descendant(child, parent)

    def handle_statement(self, text):
        text = text.strip().rstrip('.')
        
        # A is the father of B
        m = re.match(r"^([A-Z][a-z]*) is the father of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'female':
                return "That's impossible!"
            self.gender[a] = 'male'
            return self.add_parent(a, b)
            
        # A is the mother of B
        m = re.match(r"^([A-Z][a-z]*) is the mother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'male':
                return "That's impossible!"
            self.gender[a] = 'female'
            return self.add_parent(a, b)

        # A and B are the parents of C
        m = re.match(r"^([A-Z][a-z]*) and ([A-Z][a-z]*) are the parents of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c = m.groups()
            if a == c or b == c:
                return "That's impossible!"
            if self.would_create_cycle(a, c) or self.would_create_cycle(b, c):
                return "That's impossible!"
            self.parent.setdefault(c, set()).add(a)
            self.parent.setdefault(c, set()).add(b)
            return "OK! I learned something."

        # A and B are siblings
        m = re.match(r"^([A-Z][a-z]*) and ([A-Z][a-z]*) are siblings$", text)
        if m:
            a, b = m.groups()
            if a == b:
                return "That's impossible!"
            # Check if they share a parent
            parents_a = self.parent.get(a, set())
            parents_b = self.parent.get(b, set())
            if not parents_a.intersection(parents_b):
                return "That's impossible!"
            return "OK! I learned something."

        # A is a brother of B
        m = re.match(r"^([A-Z][a-z]*) is a brother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'female':
                return "That's impossible!"
            self.gender[a] = 'male'
            # Check if they share a parent
            parents_a = self.parent.get(a, set())
            parents_b = self.parent.get(b, set())
            if not parents_a.intersection(parents_b):
                return "That's impossible!"
            return "OK! I learned something."

        # A is a sister of B
        m = re.match(r"^([A-Z][a-z]*) is a sister of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'male':
                return "That's impossible!"
            self.gender[a] = 'female'
            # Check if they share a parent
            parents_a = self.parent.get(a, set())
            parents_b = self.parent.get(b, set())
            if not parents_a.intersection(parents_b):
                return "That's impossible!"
            return "OK! I learned something."

        # A is a grandmother of B
        m = re.match(r"^([A-Z][a-z]*) is a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'male':
                return "That's impossible!"
            self.gender[a] = 'female'
            # Check if grandparent relationship exists
            if not self.is_grandparent(a, b):
                return "That's impossible!"
            return "OK! I learned something."

        # A is a grandfather of B
        m = re.match(r"^([A-Z][a-z]*) is a grandfather of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'female':
                return "That's impossible!"
            self.gender[a] = 'male'
            # Check if grandparent relationship exists
            if not self.is_grandparent(a, b):
                return "That's impossible!"
            return "OK! I learned something."

        # A is a child of B
        m = re.match(r"^([A-Z][a-z]*) is a child of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return self.add_parent(b, a)

        # A is a daughter of B
        m = re.match(r"^([A-Z][a-z]*) is a daughter of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'male':
                return "That's impossible!"
            self.gender[a] = 'female'
            return self.add_parent(b, a)

        # A is a son of B
        m = re.match(r"^([A-Z][a-z]*) is a son of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'female':
                return "That's impossible!"
            self.gender[a] = 'male'
            return self.add_parent(b, a)

        # A is an uncle of B
        m = re.match(r"^([A-Z][a-z]*) is an uncle of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'female':
                return "That's impossible!"
            self.gender[a] = 'male'
            # Check if uncle relationship is valid
            if not self.is_uncle_aunt(a, b):
                return "That's impossible!"
            return "OK! I learned something."

        # A is an aunt of B
        m = re.match(r"^([A-Z][a-z]*) is an aunt of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            if self.gender.get(a) == 'male':
                return "That's impossible!"
            self.gender[a] = 'female'
            # Check if aunt relationship is valid
            if not self.is_uncle_aunt(a, b):
                return "That's impossible!"
            return "OK! I learned something."

        # Handle multiple children patterns: A, B and C are children of D
        m = re.match(r"^([A-Z][a-z]*(?:, [A-Z][a-z]*)*) and ([A-Z][a-z]*) are children of ([A-Z][a-z]*)$", text)
        if m:
            children_str, last_child, parent = m.groups()
            children_list = [c.strip() for c in children_str.split(',')]
            children_list.append(last_child)
            
            for child in children_list:
                if child == parent:
                    return "That's impossible!"
                if self.would_create_cycle(parent, child):
                    return "That's impossible!"
                self.parent.setdefault(child, set()).add(parent)
            return "OK! I learned something."

        return "I don't understand that statement."

    def is_parent(self, a, b):
        return a in self.parent.get(b, set())

    def is_grandparent(self, a, b):
        # Check if a is parent of someone who is parent of b
        for middle in self.parent.get(b, set()):
            if self.is_parent(a, middle):
                return True
        return False

    def is_sibling(self, a, b):
        if a == b:
            return False
        parents_a = self.parent.get(a, set())
        parents_b = self.parent.get(b, set())
        return bool(parents_a.intersection(parents_b))

    def is_uncle_aunt(self, a, b):
        # a is uncle/aunt of b if a is sibling of any parent of b
        for parent in self.parent.get(b, set()):
            if self.is_sibling(a, parent):
                return True
        return False

    def handle_question(self, text):
        text = text.strip().rstrip('?')
        
        # Is A the father of B?
        m = re.match(r"^Is ([A-Z][a-z]*) the father of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_parent(a, b) and self.gender.get(a) == 'male' else "No."
            
        # Is A the mother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) the mother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_parent(a, b) and self.gender.get(a) == 'female' else "No."
            
        # Is A a grandfather of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a grandfather of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_grandparent(a, b) and self.gender.get(a) == 'male' else "No."
            
        # Is A a grandmother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_grandparent(a, b) and self.gender.get(a) == 'female' else "No."

        # Who are the parents of C?
        m = re.match(r"^Who are the parents of ([A-Z][a-z]*)$", text)
        if m:
            (child,) = m.groups()
            parents = self.parent.get(child, set())
            if not parents:
                return f"No parents of {child} found."
            parents_display = ", ".join(sorted(parents))
            return f"Parents of {child}: {parents_display}."

        # Who is the mother of C?
        m = re.match(r"^Who is the mother of ([A-Z][a-z]*)$", text)
        if m:
            (child,) = m.groups()
            parents = self.parent.get(child, set())
            mothers = [p for p in parents if self.gender.get(p) == 'female']
            if not mothers:
                return f"No mother of {child} found."
            return f"Mother of {child}: {mothers[0]}."

        # Who is the father of C?
        m = re.match(r"^Who is the father of ([A-Z][a-z]*)$", text)
        if m:
            (child,) = m.groups()
            parents = self.parent.get(child, set())
            fathers = [p for p in parents if self.gender.get(p) == 'male']
            if not fathers:
                return f"No father of {child} found."
            return f"Father of {child}: {fathers[0]}."

        # Are A and B siblings?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) siblings$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_sibling(a, b) else "No."

        # Who are the siblings of X?
        m = re.match(r"^Who are the siblings of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            siblings = []
            # Get all known people
            all_people = set()
            all_people.update(self.gender.keys())
            all_people.update(self.parent.keys())
            for parents in self.parent.values():
                all_people.update(parents)
            
            for other_person in all_people:
                if other_person != person and self.is_sibling(person, other_person):
                    siblings.append(other_person)
            
            if not siblings:
                return f"No siblings of {person} found."
            return f"Siblings of {person}: " + ", ".join(sorted(siblings)) + "."

        # Is A a brother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a brother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_sibling(a, b) and self.gender.get(a) == 'male' else "No."

        # Is A a sister of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a sister of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_sibling(a, b) and self.gender.get(a) == 'female' else "No."

        # Who are the brothers of X?
        m = re.match(r"^Who are the brothers of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            brothers = []
            # Check all known people
            all_people = set()
            all_people.update(self.gender.keys())
            all_people.update(self.parent.keys())
            for parents in self.parent.values():
                all_people.update(parents)
            
            for other_person in all_people:
                if (other_person != person and 
                    self.is_sibling(person, other_person) and 
                    self.gender.get(other_person) == 'male'):
                    brothers.append(other_person)
            
            if not brothers:
                return f"No brothers of {person} found."
            return f"Brothers of {person}: " + ", ".join(sorted(brothers)) + "."

        # Who are the sisters of X?
        m = re.match(r"^Who are the sisters of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            sisters = []
            # Check all known people
            all_people = set()
            all_people.update(self.gender.keys())
            all_people.update(self.parent.keys())
            for parents in self.parent.values():
                all_people.update(parents)
            
            for other_person in all_people:
                if (other_person != person and 
                    self.is_sibling(person, other_person) and 
                    self.gender.get(other_person) == 'female'):
                    sisters.append(other_person)
            
            if not sisters:
                return f"No sisters of {person} found."
            return f"Sisters of {person}: " + ", ".join(sorted(sisters)) + "."

        # Is A an uncle of B?
        m = re.match(r"^Is ([A-Z][a-z]*) an uncle of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_uncle_aunt(a, b) and self.gender.get(a) == 'male' else "No."

        # Is A an aunt of B?
        m = re.match(r"^Is ([A-Z][a-z]*) an aunt of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_uncle_aunt(a, b) and self.gender.get(a) == 'female' else "No."

        # Who are the uncles of X?
        m = re.match(r"^Who are the uncles of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            uncles = []
            # Get all known people
            all_people = set()
            all_people.update(self.gender.keys())
            all_people.update(self.parent.keys())
            for parents in self.parent.values():
                all_people.update(parents)
            
            for other_person in all_people:
                if (self.is_uncle_aunt(other_person, person) and 
                    self.gender.get(other_person) == 'male'):
                    uncles.append(other_person)
            
            if not uncles:
                return f"No uncles of {person} found."
            return f"Uncles of {person}: " + ", ".join(sorted(uncles)) + "."

        # Who are the aunts of X?
        m = re.match(r"^Who are the aunts of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            aunts = []
            # Get all known people
            all_people = set()
            all_people.update(self.gender.keys())
            all_people.update(self.parent.keys())
            for parents in self.parent.values():
                all_people.update(parents)
            
            for other_person in all_people:
                if (self.is_uncle_aunt(other_person, person) and 
                    self.gender.get(other_person) == 'female'):
                    aunts.append(other_person)
            
            if not aunts:
                return f"No aunts of {person} found."
            return f"Aunts of {person}: " + ", ".join(sorted(aunts)) + "."

        # Is A a daughter of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a daughter of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_parent(b, a) and self.gender.get(a) == 'female' else "No."

        # Is A a son of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a son of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_parent(b, a) and self.gender.get(a) == 'male' else "No."

        # Is A a child of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a child of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_parent(b, a) else "No."

        # Who are the daughters of X?
        m = re.match(r"^Who are the daughters of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            daughters = []
            for child in self.parent.keys():
                if self.is_parent(person, child) and self.gender.get(child) == 'female':
                    daughters.append(child)
            
            if not daughters:
                return f"No daughters of {person} found."
            return f"Daughters of {person}: " + ", ".join(sorted(daughters)) + "."

        # Who are the sons of X?
        m = re.match(r"^Who are the sons of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            sons = []
            for child in self.parent.keys():
                if self.is_parent(person, child) and self.gender.get(child) == 'male':
                    sons.append(child)
            
            if not sons:
                return f"No sons of {person} found."
            return f"Sons of {person}: " + ", ".join(sorted(sons)) + "."

        # Who are the children of X?
        m = re.match(r"^Who are the children of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            children = []
            for child in self.parent.keys():
                if self.is_parent(person, child):
                    children.append(child)
            
            if not children:
                return f"No children of {person} found."
            return f"Children of {person}: " + ", ".join(sorted(children)) + "."

        # Are A and B the parents of C?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) the parents of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c = m.groups()
            parents_c = self.parent.get(c, set())
            return "Yes." if a in parents_c and b in parents_c else "No."

        # Are A, B and C children of D?
        m = re.match(r"^Are ([A-Z][a-z]*), ([A-Z][a-z]*) and ([A-Z][a-z]*) children of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c, d = m.groups()
            return "Yes." if (self.is_parent(d, a) and 
                            self.is_parent(d, b) and 
                            self.is_parent(d, c)) else "No."

        # Are A and B relatives?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) relatives$", text)
        if m:
            a, b = m.groups()
            # Check various relationships
            if (self.is_parent(a, b) or self.is_parent(b, a) or
                self.is_sibling(a, b) or
                self.is_grandparent(a, b) or self.is_grandparent(b, a) or
                self.is_uncle_aunt(a, b) or self.is_uncle_aunt(b, a)):
                return "Yes."
            return "No."

        return "I don't understand that question."

    def handle_input(self, text):
        text = text.strip()
        if text.endswith('.'):
            return self.handle_statement(text)
        elif text.endswith('?'):
            return self.handle_question(text)
        else:
            return "Please end statements with '.' and questions with '?'."

def demo():
    bot = SimpleFamilyChatbot()
    examples = [
        "Bob is the father of Alice.",
        "Alice is the mother of John.",
        "Is Bob a grandfather of John?",
        "Is Alice a grandmother of John?",
        "Is Bob the father of Alice?",
        "Is Alice the mother of John?",
        "Mark is the father of Patricia.",
        "Mark is a daughter of Ann.",  # This should be impossible
        "One is the father of Two.",
        "Two is the father of Three.",
        "Three is the father of One.",  # This should create a cycle
        "Lea is the mother of Lea."     # Self-parent impossible
    ]
    for e in examples:
        print(f"> {e}")
        print(bot.handle_input(e))
        print()

if __name__ == "__main__":
    demo()