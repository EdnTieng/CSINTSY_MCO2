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
        list(self.prolog.query("dynamic male/1."))
        list(self.prolog.query("dynamic female/1."))

        # parent comes from father or mother
        self.prolog.assertz("parent(X,Y) :- father(X,Y)")
        self.prolog.assertz("parent(X,Y) :- mother(X,Y)")
        
        # sibling relationship
        self.prolog.assertz("sibling(X,Y) :- parent(P,X), parent(P,Y), X \\= Y")
        
        # gender-specific sibling relationships
        self.prolog.assertz("brother(X,Y) :- sibling(X,Y), male(X)")
        self.prolog.assertz("sister(X,Y) :- sibling(X,Y), female(X)")
        
        # uncle and aunt relationships
        self.prolog.assertz("uncle(X,Y) :- parent(P,Y), sibling(X,P), male(X)")
        self.prolog.assertz("aunt(X,Y) :- parent(P,Y), sibling(X,P), female(X)")

        # grandparent relationships
        self.prolog.assertz("grandparent(X,Y) :- parent(X,Z), parent(Z,Y)")
        self.prolog.assertz("grandfather(X,Y) :- grandparent(X,Y), male(X)")
        self.prolog.assertz("grandmother(X,Y) :- grandparent(X,Y), female(X)")
        
        # child relationships (inverse of parent)
        self.prolog.assertz("child(X,Y) :- parent(Y,X)")
        self.prolog.assertz("son(X,Y) :- child(X,Y), male(X)")
        self.prolog.assertz("daughter(X,Y) :- child(X,Y), female(X)")
        
        # ancestor relationship (transitive closure of parent)
        self.prolog.assertz("ancestor(X,Y) :- parent(X,Y)")
        self.prolog.assertz("ancestor(X,Y) :- parent(X,Z), ancestor(Z,Y)")
        
        # relative relationship (symmetric)
        self.prolog.assertz("relative(X,Y) :- parent(X,Y)")
        self.prolog.assertz("relative(X,Y) :- parent(Y,X)")
        self.prolog.assertz("relative(X,Y) :- sibling(X,Y)")
        self.prolog.assertz("relative(X,Y) :- grandparent(X,Y)")
        self.prolog.assertz("relative(X,Y) :- grandparent(Y,X)")
        self.prolog.assertz("relative(X,Y) :- uncle(X,Y)")
        self.prolog.assertz("relative(X,Y) :- aunt(X,Y)")
        self.prolog.assertz("relative(X,Y) :- uncle(Y,X)")
        self.prolog.assertz("relative(X,Y) :- aunt(Y,X)")

    def _assert_parent(self, parent_atom, child_atom):
        if parent_atom == child_atom:
            return False, "That's impossible!"
        # cycle detection: if child is already ancestor of parent
        if list(self.prolog.query(f"ancestor({child_atom},{parent_atom})")):
            return False, "That's impossible!"
        self.prolog.assertz(f"parent({parent_atom},{child_atom})")
        return True, None

    def _enforce_gender(self, person_atom, gender):
        existing = self.gender.get(person_atom)
        if existing and existing != gender:
            return False, "That's impossible!"
        
        # Check if contradicts existing Prolog facts
        if gender == 'male' and list(self.prolog.query(f"female({person_atom})")):
            return False, "That's impossible!"
        if gender == 'female' and list(self.prolog.query(f"male({person_atom})")):
            return False, "That's impossible!"
            
        self.gender[person_atom] = gender
        if gender == 'male':
            self.prolog.assertz(f"male({person_atom})")
        else:
            self.prolog.assertz(f"female({person_atom})")
        return True, None

    def handle_statement(self, text):
        text = text.strip().rstrip('.')
        
        # A is the father of B
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
            self.prolog.assertz(f"father({a_p},{b_p})")
            return "OK! I learned something."

        # A is the mother of B
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
            self.prolog.assertz(f"mother({a_p},{b_p})")
            return "OK! I learned something."
        
        # A and B are the parents of C
        m = re.match(r"^([A-Z][a-z]*) and ([A-Z][a-z]*) are the parents of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            c_p = norm(c)
            # check reflexive/cycle for each parent
            if a_p == c_p or b_p == c_p:
                return "That's impossible!"
            if list(self.prolog.query(f"ancestor({c_p},{a_p})")) or list(self.prolog.query(f"ancestor({c_p},{b_p})")):
                return "That's impossible!"
            # assert both parents
            self.prolog.assertz(f"parent({a_p},{c_p})")
            self.prolog.assertz(f"parent({b_p},{c_p})")
            return "OK! I learned something."

        # A and B are siblings
        m = re.match(r"^([A-Z][a-z]*) and ([A-Z][a-z]*) are siblings$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            if a_p == b_p:
                return "That's impossible!"
            # check for existing common parent
            sols = list(self.prolog.query(f"parent(P,{a_p}), parent(P,{b_p})"))
            if sols:
                return "OK! I learned something."  # already entailed
            else:
                return "That's impossible!"

        # A is a brother of B
        m = re.match(r"^([A-Z][a-z]*) is a brother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            # enforce male
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            # check they share a parent
            common = list(self.prolog.query(f"parent(P,{a_p}), parent(P,{b_p})"))
            if not common:
                return "That's impossible!"
            return "OK! I learned something."

        # A is a sister of B
        m = re.match(r"^([A-Z][a-z]*) is a sister of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            common = list(self.prolog.query(f"parent(P,{a_p}), parent(P,{b_p})"))
            if not common:
                return "That's impossible!"
            return "OK! I learned something."

        # A is a grandmother of B
        m = re.match(r"^([A-Z][a-z]*) is a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            # Check if grandparent relationship is valid
            sols = list(self.prolog.query(f"parent({a_p},Z), parent(Z,{b_p})"))
            if not sols:
                return "That's impossible!"
            return "OK! I learned something."

        # A is a grandfather of B
        m = re.match(r"^([A-Z][a-z]*) is a grandfather of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            # Check if grandparent relationship is valid
            sols = list(self.prolog.query(f"parent({a_p},Z), parent(Z,{b_p})"))
            if not sols:
                return "That's impossible!"
            return "OK! I learned something."

        # A is a child of B
        m = re.match(r"^([A-Z][a-z]*) is a child of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._assert_parent(b_p, a_p)
            if not ok:
                return err
            return "OK! I learned something."

        # A is a daughter of B
        m = re.match(r"^([A-Z][a-z]*) is a daughter of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            ok2, err2 = self._assert_parent(b_p, a_p)
            if not ok2:
                return err2
            return "OK! I learned something."

        # A is a son of B
        m = re.match(r"^([A-Z][a-z]*) is a son of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            ok2, err2 = self._assert_parent(b_p, a_p)
            if not ok2:
                return err2
            return "OK! I learned something."

        # A is an uncle of B
        m = re.match(r"^([A-Z][a-z]*) is an uncle of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            # verify logical plausibility: there exists P parent of B such that sibling(a,P)
            sols = list(self.prolog.query(f"parent(P,{b_p}), sibling({a_p},P)"))
            if not sols:
                return "That's impossible!"
            return "OK! I learned something."

        # A is an aunt of B
        m = re.match(r"^([A-Z][a-z]*) is an aunt of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            sols = list(self.prolog.query(f"parent(P,{b_p}), sibling({a_p},P)"))
            if not sols:
                return "That's impossible!"
            return "OK! I learned something."

        # A, B and C are children of D (and variations with more children)
        m = re.match(r"^([A-Z][a-z]*(?:, [A-Z][a-z]*)*) and ([A-Z][a-z]*) are children of ([A-Z][a-z]*)$", text)
        if m:
            children_str, last_child, parent = m.groups()
            children_list = [c.strip() for c in children_str.split(',')]
            children_list.append(last_child)
            parent_p = norm(parent)
            
            for child in children_list:
                child_p = norm(child)
                ok, err = self._assert_parent(parent_p, child_p)
                if not ok:
                    return err
            return "OK! I learned something."

        return "I don't understand that statement."

    def handle_question(self, text):
        text = text.strip().rstrip('?')
        
        # Is A the father of B?
        m = re.match(r"^Is ([A-Z][a-z]*) the father of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"father({a_p},{b_p})")) else "No."

        # Is A the mother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) the mother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"mother({a_p},{b_p})")) else "No."

        # Is A a grandfather of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a grandfather of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"grandfather({a_p},{b_p})")) else "No."

        # Is A a grandmother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"grandmother({a_p},{b_p})")) else "No."

        # Who are the parents of C?
        m = re.match(r"^Who are the parents of ([A-Z][a-z]*)$", text)
        if m:
            (child,) = m.groups()
            child_p = norm(child)
            sols = list(self.prolog.query(f"parent(X,{child_p})"))
            if not sols:
                return f"No parents of {child} found."
            parents = sorted({sol['X'] for sol in sols})
            parents_display = ", ".join(p.capitalize() for p in parents)
            return f"Parents of {child}: {parents_display}."

        # Who is the mother of C?
        m = re.match(r"^Who is the mother of ([A-Z][a-z]*)$", text)
        if m:
            (child,) = m.groups()
            child_p = norm(child)
            sols = list(self.prolog.query(f"mother(X,{child_p})"))
            if not sols:
                return f"No mother of {child} found."
            mother = sols[0]['X']
            return f"Mother of {child}: {mother.capitalize()}."

        # Who is the father of C?
        m = re.match(r"^Who is the father of ([A-Z][a-z]*)$", text)
        if m:
            (child,) = m.groups()
            child_p = norm(child)
            sols = list(self.prolog.query(f"father(X,{child_p})"))
            if not sols:
                return f"No father of {child} found."
            father = sols[0]['X']
            return f"Father of {child}: {father.capitalize()}."

        # Are A and B siblings?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) siblings$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"sibling({a_p},{b_p})")) else "No."

        # Who are the siblings of X?
        m = re.match(r"^Who are the siblings of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"sibling(X,{p})"))
            if not sols:
                return f"No siblings of {person} found."
            siblings = sorted({sol['X'] for sol in sols})
            sib_display = ", ".join(s.capitalize() for s in siblings)
            return f"Siblings of {person}: {sib_display}."

        # Is A a brother of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a brother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"brother({a_p},{b_p})")) else "No."

        # Is A a sister of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a sister of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"sister({a_p},{b_p})")) else "No."

        # Who are the brothers of X?
        m = re.match(r"^Who are the brothers of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"brother(X,{p})"))
            if not sols:
                return f"No brothers of {person} found."
            brothers = sorted({sol['X'] for sol in sols})
            return f"Brothers of {person}: " + ", ".join(b.capitalize() for b in brothers) + "."

        # Who are the sisters of X?
        m = re.match(r"^Who are the sisters of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"sister(X,{p})"))
            if not sols:
                return f"No sisters of {person} found."
            sisters = sorted({sol['X'] for sol in sols})
            return f"Sisters of {person}: " + ", ".join(s.capitalize() for s in sisters) + "."

        # Is A an uncle of B?
        m = re.match(r"^Is ([A-Z][a-z]*) an uncle of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"uncle({a_p},{b_p})")) else "No."

        # Is A an aunt of B?
        m = re.match(r"^Is ([A-Z][a-z]*) an aunt of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"aunt({a_p},{b_p})")) else "No."

        # Who are the uncles of X?
        m = re.match(r"^Who are the uncles of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"uncle(X,{p})"))
            if not sols:
                return f"No uncles of {person} found."
            uncles = sorted({sol['X'] for sol in sols})
            return f"Uncles of {person}: " + ", ".join(u.capitalize() for u in uncles) + "."

        # Who are the aunts of X?
        m = re.match(r"^Who are the aunts of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"aunt(X,{p})"))
            if not sols:
                return f"No aunts of {person} found."
            aunts = sorted({sol['X'] for sol in sols})
            return f"Aunts of {person}: " + ", ".join(a.capitalize() for a in aunts) + "."

        # Is A a daughter of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a daughter of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"daughter({a_p},{b_p})")) else "No."

        # Is A a son of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a son of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"son({a_p},{b_p})")) else "No."

        # Is A a child of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a child of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"child({a_p},{b_p})")) else "No."

        # Who are the daughters of X?
        m = re.match(r"^Who are the daughters of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"daughter(X,{p})"))
            if not sols:
                return f"No daughters of {person} found."
            daughters = sorted({sol['X'] for sol in sols})
            return f"Daughters of {person}: " + ", ".join(d.capitalize() for d in daughters) + "."

        # Who are the sons of X?
        m = re.match(r"^Who are the sons of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"son(X,{p})"))
            if not sols:
                return f"No sons of {person} found."
            sons = sorted({sol['X'] for sol in sols})
            return f"Sons of {person}: " + ", ".join(s.capitalize() for s in sons) + "."

        # Who are the children of X?
        m = re.match(r"^Who are the children of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"child(X,{p})"))
            if not sols:
                return f"No children of {person} found."
            children = sorted({sol['X'] for sol in sols})
            return f"Children of {person}: " + ", ".join(c.capitalize() for c in children) + "."

        # Are A and B the parents of C?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) the parents of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            c_p = norm(c)
            sols_a = list(self.prolog.query(f"parent({a_p},{c_p})"))
            sols_b = list(self.prolog.query(f"parent({b_p},{c_p})"))
            return "Yes." if sols_a and sols_b else "No."

        # Are A, B and C children of D?
        m = re.match(r"^Are ([A-Z][a-z]*), ([A-Z][a-z]*) and ([A-Z][a-z]*) children of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c, d = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            c_p = norm(c)
            d_p = norm(d)
            sols_a = list(self.prolog.query(f"child({a_p},{d_p})"))
            sols_b = list(self.prolog.query(f"child({b_p},{d_p})"))
            sols_c = list(self.prolog.query(f"child({c_p},{d_p})"))
            return "Yes." if sols_a and sols_b and sols_c else "No."

        # Are A and B relatives?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) relatives$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"relative({a_p},{b_p})")) else "No."

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