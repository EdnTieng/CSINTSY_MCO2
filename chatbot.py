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
        self.prolog.assertz("sibling(X,Y) :- parent(P,X), parent(P,Y), X \\= Y")
        self.prolog.assertz("uncle(X,Y) :- parent(P,Y), sibling(X,P), male(X)")
        self.prolog.assertz("aunt(X,Y) :- parent(P,Y), sibling(X,P), female(X)")

        # ancestor and grandparent inference
        self.prolog.assertz("ancestor(X,Y) :- parent(X,Y)")
        self.prolog.assertz("ancestor(X,Y) :- parent(X,Z), ancestor(Z,Y)")
        self.prolog.assertz("grandparent(X,Y) :- parent(X,Z), parent(Z,Y)")
        self.prolog.assertz("grandfather(X,Y) :- grandparent(X,Y), male(X)")
        self.prolog.assertz("grandmother(X,Y) :- grandparent(X,Y), female(X)")
        self.prolog.assertz("sibling(X,Y) :- parent(P,X), parent(P,Y), X \\= Y")

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
        # New pattern: "A and B are the parents of C"
        m = re.match(r"^([A-Z][a-z]*) and ([A-Z][a-z]*) are the parents of ([A-Z][a-z]*)$", text)
        if m:
            a, b, c = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            c_p = norm(c)
            # check reflexive/cycle for each parent
            if a_p == c_p or b_p == c_p:
                return "Impossible: someone cannot be their own parent."
            if list(self.prolog.query(f"ancestor({c_p},{a_p})")) or list(self.prolog.query(f"ancestor({c_p},{b_p})")):
                return "Impossible: this would create a cycle."
            # assert both parents
            self.prolog.assertz(f"parent({a_p},{c_p})")
            self.prolog.assertz(f"parent({b_p},{c_p})")
            return "OK! Learned parents relation."

        # existing father/mother cases...
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
            self.prolog.assertz(f"mother({a_p},{b_p})")
            return "OK! Learned mother relation."
        
        # "A is the mother of B and C."
        m = re.match(r"^([A-Z][a-z]*) is the mother of ([A-Z][a-z]*) and ([A-Z][a-z]*)$", text)
        if m:
            mom, child1, child2 = m.groups()
            mom_p = norm(mom)
            c1_p = norm(child1)
            c2_p = norm(child2)
            ok, err = self._enforce_gender(mom_p, 'female')
            if not ok:
                return err
            # add both mother relationships (which imply parent)
            # you can reuse _assert_parent to check cycles/reflexive if desired
            ok1, err1 = self._assert_parent(mom_p, c1_p)
            if not ok1:
                return err1
            self.prolog.assertz(f"mother({mom_p},{c1_p})")
            ok2, err2 = self._assert_parent(mom_p, c2_p)
            if not ok2:
                return err2
            self.prolog.assertz(f"mother({mom_p},{c2_p})")
            return "OK! Learned mother of both."

        # "A and B are siblings." only allowed if they share a known parent
        m = re.match(r"^([A-Z][a-z]*) and ([A-Z][a-z]*) are siblings$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            if a_p == b_p:
                return "Impossible: someone cannot be sibling of themselves."
            # check for existing common parent
            sols = list(self.prolog.query(f"parent(P,{a_p}), parent(P,{b_p})"))
            if sols:
                return "OK! They are siblings."  # already entailed
            else:
                return ("Impossible: cannot declare them siblings without a shared parent. "
                        "First give a parent, e.g., 'A is the mother of B and C.'")
        # "A is a brother of B."
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
                return ("Impossible: cannot declare brother if no shared parent is known. "
                        "First provide a parent for both.")
            return "OK! Learned brother relation."  # siblinghood already implied

        # "A is a sister of B."
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
                return ("Impossible: cannot declare sister if no shared parent is known. "
                        "First provide a parent for both.")
            return "OK! Learned sister relation."
        # "A is an uncle of B."
        m = re.match(r"^([A-Z][a-z]*) is an uncle of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            # verify logical plausibility: there exists P parent of B such that sibling(a,P)
            sols = list(self.prolog.query(f"parent(P,{norm(b)}), sibling({a_p},P)"))
            if not sols:
                return ("Impossible: to declare uncle, the person must be a sibling of a parent. "
                        "Ensure the parent and sibling relationships exist.")
            # now assert the explicit uncle fact so future questions succeed
            self.prolog.assertz(f"uncle({a_p},{norm(b)})")
            return "OK! Learned uncle relation."


        # "A is an aunt of B."
        m = re.match(r"^([A-Z][a-z]*) is an aunt of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            sols = list(self.prolog.query(f"parent(P,{norm(b)}), sibling({a_p},P)"))
            if not sols:
                return ("Impossible: to declare aunt, the person must be a sibling of a parent. "
                        "Ensure the parent and sibling relationships exist.")
            return "OK! Learned aunt relation."

        # "A is a child of B."
        m = re.match(r"^([A-Z][a-z]*) is a child of ([A-Z][a-z]*)$", text)
        if m:
            child, parent = m.groups()
            c_p = norm(child)
            p_p = norm(parent)
            if c_p == p_p:
                return "Impossible: someone cannot be their own parent."
            if list(self.prolog.query(f"ancestor({c_p},{p_p})")):
                return "Impossible: this would create a cycle."
            self.prolog.assertz(f"parent({p_p},{c_p})")
            return "OK! Learned child-parent relation."

        # "A is a daughter of B." or "A is a son of B."
        m = re.match(r"^([A-Z][a-z]*) is a (daughter|son) of ([A-Z][a-z]*)$", text)
        if m:
            child, gender_word, parent = m.groups()
            c_p = norm(child)
            p_p = norm(parent)
            gender = 'female' if gender_word == 'daughter' else 'male'
            ok, err = self._enforce_gender(c_p, gender)
            if not ok:
                return err
            if c_p == p_p:
                return "Impossible: someone cannot be their own parent."
            if list(self.prolog.query(f"ancestor({c_p},{p_p})")):
                return "Impossible: this would create a cycle."
            self.prolog.assertz(f"parent({p_p},{c_p})")
            return f"OK! Learned {gender_word} relation."
        
        # "A, B, and C are children of D."
        m = re.match(r"^([A-Z][a-z]*(?:, [A-Z][a-z]*)*(?: and [A-Z][a-z]*)?) are children of ([A-Z][a-z]*)$", text)
        if m:
            children_str, parent = m.groups()
            parent_p = norm(parent)
            names = [norm(name.strip()) for name in re.split(r", | and ", children_str)]
            for child_p in names:
                if child_p == parent_p:
                    return "Impossible: someone cannot be their own parent."
                if list(self.prolog.query(f"ancestor({child_p},{parent_p})")):
                    return "Impossible: this would create a cycle."
                self.prolog.assertz(f"parent({parent_p},{child_p})")
            return "OK! Learned children-parent relations."

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

        # e.g., "Who are the parents of C?"
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
            sibling_check = list(self.prolog.query(f"parent(P,{a_p}), parent(P,{b_p})"))
            is_male = self.gender.get(a_p) == 'male' or bool(list(self.prolog.query(f"male({a_p})")))
            return "Yes." if sibling_check and is_male else "No."

        # Is A a sister of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a sister of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            sibling_check = list(self.prolog.query(f"parent(P,{a_p}), parent(P,{b_p})"))
            is_female = self.gender.get(a_p) == 'female' or bool(list(self.prolog.query(f"female({a_p})")))
            return "Yes." if sibling_check and is_female else "No."

        # Who are the brothers of X?
        m = re.match(r"^Who are the brothers of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"parent(P,{p}), parent(P,X), X \\= {p}"))
            brothers = []
            for sol in sols:
                candidate = sol['X']
                if (self.gender.get(candidate) == 'male' or bool(list(self.prolog.query(f"male({candidate})")))) \
                and any(list(self.prolog.query(f"parent(P,{candidate}), parent(P,{p})"))):
                    brothers.append(candidate)
            if not brothers:
                return f"No brothers of {person} found."
            return f"Brothers of {person}: " + ", ".join(b.capitalize() for b in sorted(set(brothers))) + "."

        # Who are the sisters of X?
        m = re.match(r"^Who are the sisters of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"parent(P,{p}), parent(P,X), X \\= {p}"))
            sisters = []
            for sol in sols:
                candidate = sol['X']
                if (self.gender.get(candidate) == 'female' or bool(list(self.prolog.query(f"female({candidate})")))) \
                and any(list(self.prolog.query(f"parent(P,{candidate}), parent(P,{p})"))):
                    sisters.append(candidate)
            if not sisters:
                return f"No sisters of {person} found."
            return f"Sisters of {person}: " + ", ".join(s.capitalize() for s in sorted(set(sisters))) + "."

        # Is A an uncle of B?
        m = re.match(r"^Is ([A-Z][a-z]*) an uncle of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            # structural check
            structural = bool(list(self.prolog.query(f"parent(P,{norm(b)}), sibling({a_p},P)")))
            if not structural:
                return "No."
            known = self.gender.get(a_p)
            if known == 'female':
                return "No."
            if known == 'male':
                return "Yes."
            return "Probably."

        # Is A an aunt of B?
        m = re.match(r"^Is ([A-Z][a-z]*) an aunt of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            structural = bool(list(self.prolog.query(f"parent(P,{norm(b)}), sibling({a_p},P)")))
            if not structural:
                return "No."
            known = self.gender.get(a_p)
            if known == 'male':
                return "No."
            if known == 'female':
                return "Yes."
            return "Probably."

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

        # Is A a daughter/son/child of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a (daughter|son|child) of ([A-Z][a-z]*)$", text)
        if m:
            child, role, parent = m.groups()
            c_p = norm(child)
            p_p = norm(parent)
            if role == 'child':
                return "Yes." if list(self.prolog.query(f"parent({p_p},{c_p})")) else "No."
            gender = 'female' if role == 'daughter' else 'male'
            gender_match = self.gender.get(c_p) == gender or bool(list(self.prolog.query(f"{gender}({c_p})")))
            return "Yes." if gender_match and list(self.prolog.query(f"parent({p_p},{c_p})")) else "No."

        # Who are the daughters/sons/children of A?
        m = re.match(r"^Who are the (daughters|sons|children) of ([A-Z][a-z]*)$", text)
        if m:
            role, parent = m.groups()
            p_p = norm(parent)
            kids = list(self.prolog.query(f"parent({p_p},X)"))
            if not kids:
                return f"No {role} of {parent} found."
            children = []
            for kid in kids:
                child = kid['X']
                if role == 'children':
                    children.append(child)
                elif role == 'daughters' and (self.gender.get(child) == 'female' or bool(list(self.prolog.query(f"female({child})")))):
                    children.append(child)
                elif role == 'sons' and (self.gender.get(child) == 'male' or bool(list(self.prolog.query(f"male({child})")))):
                    children.append(child)
            if not children:
                return f"No {role} of {parent} found."
            return f"{role.capitalize()} of {parent}: " + ", ".join(c.capitalize() for c in sorted(children)) + "."

        # Are A, B, and C children of D?
        m = re.match(r"^Are ([A-Z][a-z]*(?:, [A-Z][a-z]*)*(?: and [A-Z][a-z]*)?) children of ([A-Z][a-z]*)$", text)
        if m:
            children_str, parent = m.groups()
            parent_p = norm(parent)
            names = [norm(name.strip()) for name in re.split(r", | and ", children_str)]
            for child_p in names:
                if not list(self.prolog.query(f"parent({parent_p},{child_p})")):
                    return "No."
            return "Yes."

        # Are A and B the parents of C?
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) the parents of ([A-Z][a-z]*)$", text)
        if m:
            p1, p2, child = m.groups()
            p1_p = norm(p1)
            p2_p = norm(p2)
            c_p = norm(child)
            if list(self.prolog.query(f"parent({p1_p},{c_p})")) and list(self.prolog.query(f"parent({p2_p},{c_p})")):
                return "Yes."
            return "No."

        # Who is the father/mother of A?
        m = re.match(r"^Who is the (father|mother) of ([A-Z][a-z]*)$", text)
        if m:
            role, child = m.groups()
            child_p = norm(child)
            if role == 'father':
                sols = list(self.prolog.query(f"father(X,{child_p})"))
            else:
                sols = list(self.prolog.query(f"mother(X,{child_p})"))
            if not sols:
                return f"No {role} of {child} found."
            parent = sols[0]['X']
            return f"{role.capitalize()} of {child}: {parent.capitalize()}."
        
        # Are A and B relatives?
        # This checks if they share any ancestor, parent, or sibling relationship
        m = re.match(r"^Are ([A-Z][a-z]*) and ([A-Z][a-z]*) relatives$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            # check shared ancestor
            for rel in ['ancestor', 'parent', 'sibling']:
                if list(self.prolog.query(f"{rel}(X,{a_p}), {rel}(X,{b_p})")) or \
                list(self.prolog.query(f"{rel}({a_p},{b_p})")) or \
                list(self.prolog.query(f"{rel}({b_p},{a_p})")):
                    return "Yes."
            return "No."


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
