import re

class SimpleFamilyChatbot:
    def __init__(self):
        # parent[child] = set of parents
        self.parent = {}  # child -> set of parents
        # gender[name] = 'male' or 'female'
        self.gender = {}

    def add_parent(self, parent, child):
        if parent == child:
            return "Impossible: someone cannot be their own parent."
        self.parent.setdefault(child, set()).add(parent)
        return "OK! Learned that."

    def handle_statement(self, text):
        text = text.strip().rstrip('.')
        # father
        m = re.match(r"^([A-Z][a-z]*) is the father of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            self.gender[a] = 'male'
            return self.add_parent(a, b)
        # mother
        m = re.match(r"^([A-Z][a-z]*) is the mother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            self.gender[a] = 'female'
            return self.add_parent(a, b)
        return "I don't understand that statement."

    def is_parent(self, a, b):
        return a in self.parent.get(b, set())

    def is_grandparent(self, a, b, kind):  # kind = 'grandfather' or 'grandmother'
        # check if a is parent of someone who is parent of b
        for middle in self.parent.get(b, set()):
            if self.is_parent(a, middle):
                if kind == 'grandfather' and self.gender.get(a) == 'male':
                    return True
                if kind == 'grandmother' and self.gender.get(a) == 'female':
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
            return "Yes." if self.is_grandparent(a, b, "grandfather") else "No."
        # Is A a grandmother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            return "Yes." if self.is_grandparent(a, b, "grandmother") else "No."
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
        "Is Alice the mother of John?"
    ]
    for e in examples:
        print(f"> {e}")
        print(bot.handle_input(e))
    # show negative example
    print("> Lea is the mother of Lea.")
    print(bot.handle_input("Lea is the mother of Lea."))

if __name__ == "__main__":
    demo()
