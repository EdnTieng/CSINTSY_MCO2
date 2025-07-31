import re
from pyswip import Prolog

def norm(name: str) -> str:
    """Normalize a user name to a Prolog atom (lowercase)."""
    return name.lower()

class PrologFamilyBot:
    def __init__(self):
        self.prolog = Prolog()
        self.gender = {}  
        self._load_rules()

    def _load_rules(self):
        # declare dynamics
        list(self.prolog.query("dynamic parent/2."))
        list(self.prolog.query("dynamic father/2."))
        list(self.prolog.query("dynamic mother/2."))
        list(self.prolog.query("dynamic grandfather/2."))
        list(self.prolog.query("dynamic grandmother/2."))
        list(self.prolog.query("dynamic ancestor/2."))

        # parent comes from father or mother
        self.prolog.assertz("parent(X,Y) :- father(X,Y)")
        self.prolog.assertz("parent(X,Y) :- mother(X,Y)")

        # ancestor and grandparent inference
        self.prolog.assertz("ancestor(X,Y) :- parent(X,Y)")
        self.prolog.assertz("ancestor(X,Y) :- parent(X,Z), ancestor(Z,Y)")
        self.prolog.assertz("grandparent(X,Y) :- parent(X,Z), parent(Z,Y)")
        self.prolog.assertz("grandfather(X,Y) :- grandparent(X,Y), male(X)")
        self.prolog.assertz("grandmother(X,Y) :- grandparent(X,Y), female(X)")

        # gender from direct father/mother facts
        self.prolog.assertz("male(X) :- father(X,_)")
        self.prolog.assertz("female(X) :- mother(X,_)")


    def _assert_parent(self, parent_atom, child_atom):
        if parent_atom == child_atom:
            return False, "Impossible: someone cannot be their own parent."
        # cycle detection: if child is already ancestor of parent
        if list(self.prolog.query(f"ancestor({child_atom},{parent_atom})")):
            return False, "Impossible: this would create a cycle."
        self.prolog.assertz(f"parent({parent_atom},{child_atom})")
        return True, None

    def _enforce_gender(self, person_atom, gender):
        existing = self.gender.get(person_atom)
        if existing and existing != gender:
            return False, f"Impossible: conflicting gender for {person_atom}."
        self.gender[person_atom] = gender
        return True, None

    def handle_statement(self, text):
        text = text.strip().rstrip('.')
        m = re.match(r"^([A-Z][a-z]*) is the father of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            ok2, err2 = self._assert_parent(a_p, b_p)
            if not ok2:
                return err2
            # assert father so male(X) and father(X,Y) hold
            # for father statement
            self.prolog.assertz(f"father({a_p},{b_p})")  # this also makes parent(a_p,b_p) true via rule
            return "OK! Learned father relation."

        m = re.match(r"^([A-Z][a-z]*) is the mother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            ok2, err2 = self._assert_parent(a_p, b_p)
            if not ok2:
                return err2
            # for mother statement
            self.prolog.assertz(f"mother({a_p},{b_p})")
            return "OK! Learned mother relation."

        return "I don't understand that statement."

    def handle_question(self, text):
        text = text.strip().rstrip('?')
        m = re.match(r"^Is ([A-Z][a-z]*) the father of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"father({a_p},{b_p})")) else "No."

        m = re.match(r"^Is ([A-Z][a-z]*) the mother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"mother({a_p},{b_p})")) else "No."

        m = re.match(r"^Is ([A-Z][a-z]*) a grandfather of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"grandfather({a_p},{b_p})")) else "No."

        m = re.match(r"^Is ([A-Z][a-z]*) a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"grandmother({a_p},{b_p})")) else "No."

        return "I don't understand that question."

    def handle_input(self, line):
        line = line.strip()
        if not line:
            return "Please type something."
        if line.endswith('.'):
            return self.handle_statement(line)
        elif line.endswith('?'):
            return self.handle_question(line)
        else:
            return "Statements must end with '.' and questions with '?'."

    def repl(self):
        print("Simple Prolog Family Bot. Type 'exit' to quit.")
        while True:
            try:
                inp = input("> ").strip()
            except EOFError:
                break
            if inp.lower() in ('exit', 'quit'):
                print("Bye.")
                break
            print(self.handle_input(inp))


if __name__ == "__main__":
    bot = PrologFamilyBot()
    bot.repl()
