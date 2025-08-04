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

        # relative inference
        self.prolog.assertz("relative(X,Y) :- ancestor(X,Y)")
        self.prolog.assertz("relative(X,Y) :- ancestor(Y,X)")
        self.prolog.assertz("relative(X,Y) :- parent(P,X), parent(P,Y), X \\= Y")
        self.prolog.assertz("relative(X,Y) :- ancestor(A,X), ancestor(A,Y), X \\= Y")

        #children inference
        self.prolog.assertz("child(X,Y) :- parent(Y,X)")
        self.prolog.assertz("daughter(X,Y) :- parent(Y,X), female(X)")
        self.prolog.assertz("son(X,Y) :- parent(Y,X), male(X)")

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

        # "A is a child of B."
        m = re.match(r"^([A-Z][a-z]*) is a child of ([A-Z][a-z]*)$", text)
        if m:
            child, parent = m.groups()
            child_p = norm(child)
            parent_p = norm(parent)
            # basic reflexive/cycle check
            if child_p == parent_p:
                return "Impossible: someone cannot be their own parent/child."
            if list(self.prolog.query(f"ancestor({child_p},{parent_p})")):
                return "Impossible: this would create a cycle."
            self.prolog.assertz(f"parent({parent_p},{child_p})")
            return "OK! Learned child relation."

        # "A is a daughter of B."
        m = re.match(r"^([A-Z][a-z]*) is a daughter of ([A-Z][a-z]*)$", text)
        if m:
            daughter, parent = m.groups()
            d_p = norm(daughter)
            p_p = norm(parent)
            ok, err = self._enforce_gender(d_p, 'female')
            if not ok:
                return err
            if d_p == p_p:
                return "Impossible: someone cannot be their own parent/child."
            if list(self.prolog.query(f"ancestor({d_p},{p_p})")):
                return "Impossible: this would create a cycle."
            self.prolog.assertz(f"parent({p_p},{d_p})")
            return "OK! Learned daughter relation."

        # "A is a son of B."
        m = re.match(r"^([A-Z][a-z]*) is a son of ([A-Z][a-z]*)$", text)
        if m:
            son, parent = m.groups()
            s_p = norm(son)
            p_p = norm(parent)
            ok, err = self._enforce_gender(s_p, 'male')
            if not ok:
                return err
            if s_p == p_p:
                return "Impossible: someone cannot be their own parent/child."
            if list(self.prolog.query(f"ancestor({s_p},{p_p})")):
                return "Impossible: this would create a cycle."
            self.prolog.assertz(f"parent({p_p},{s_p})")
            return "OK! Learned son relation."

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

        # "A is the grandfather of B."
        m = re.match(r"^([A-Z][a-z]*) is a grandfather of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            # enforce male
            ok, err = self._enforce_gender(a_p, 'male')
            if not ok:
                return err
            # require existing intermediate Z with parent(a,Z) and parent(Z,b)
            sols = list(self.prolog.query(f"parent({a_p},Z), parent(Z,{b_p})"))
            if not sols:
                return ("Impossible: cannot declare grandfather without the intermediate generation. "
                        "First supply something like 'A is the father of P.' and 'P is the parent of B.'")
            # record explicit fact so future queries succeed
            self.prolog.assertz(f"grandfather({a_p},{b_p})")
            return "OK! Learned grandfather relation."

        # "A is the grandmother of B."
        m = re.match(r"^([A-Z][a-z]*) is a grandmother of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            ok, err = self._enforce_gender(a_p, 'female')
            if not ok:
                return err
            sols = list(self.prolog.query(f"parent({a_p},Z), parent(Z,{b_p})"))
            if not sols:
                return ("Impossible: cannot declare grandmother without the intermediate generation. "
                        "First supply something like 'A is the mother of P.' and 'P is the parent of B.'")
            self.prolog.assertz(f"grandmother({a_p},{b_p})")
            return "OK! Learned grandmother relation."

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
        
        # Is A a child of B?
        m = re.match(r"^Is ([A-Z][a-z]*) a child of ([A-Z][a-z]*)$", text)
        if m:
            a, b = m.groups()
            a_p = norm(a)
            b_p = norm(b)
            return "Yes." if list(self.prolog.query(f"child({a_p},{b_p})")) else "No."

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

        # Who are the children of X?
        m = re.match(r"^Who are the children of ([A-Z][a-z]*)$", text)
        if m:
            (parent,) = m.groups()
            p = norm(parent)
            sols = list(self.prolog.query(f"child(X,{p})"))
            if not sols:
                return f"No children of {parent} found."
            children = sorted({sol['X'] for sol in sols})
            return f"Children of {parent}: " + ", ".join(c.capitalize() for c in children) + "."

        # Who are the daughters of X?
        m = re.match(r"^Who are the daughters of ([A-Z][a-z]*)$", text)
        if m:
            (parent,) = m.groups()
            p = norm(parent)
            sols = list(self.prolog.query(f"daughter(X,{p})"))
            if not sols:
                return f"No daughters of {parent} found."
            daughters = sorted({sol['X'] for sol in sols})
            return f"Daughters of {parent}: " + ", ".join(d.capitalize() for d in daughters) + "."

        # Who are the sons of X?
        m = re.match(r"^Who are the sons of ([A-Z][a-z]*)$", text)
        if m:
            (parent,) = m.groups()
            p = norm(parent)
            sols = list(self.prolog.query(f"son(X,{p})"))
            if not sols:
                return f"No sons of {parent} found."
            sons = sorted({sol['X'] for sol in sols})
            return f"Sons of {parent}: " + ", ".join(s.capitalize() for s in sons) + "."

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

        # Who are the relatives of X?
        m = re.match(r"^Who are the relatives of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            # gather both directions to cover ancestor/descendant and other cases
            sols1 = list(self.prolog.query(f"relative({p},Y)"))
            sols2 = list(self.prolog.query(f"relative(Y,{p})"))
            relatives = {sol['Y'] for sol in sols1 if sol.get('Y') and sol['Y'] != p}
            relatives.update({sol['Y'] for sol in sols2 if sol.get('Y') and sol['Y'] != p})
            if not relatives:
                return f"No relatives of {person} found."
            rel_display = ", ".join(r.capitalize() for r in sorted(relatives))
            return f"Relatives of {person}: {rel_display}."
        
        # Who are the grandfathers of X?
        m = re.match(r"^Who are the grandfathers of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"grandfather(X,{p})"))
            if not sols:
                return f"No grandfathers of {person} found."
            gfs = sorted({sol['X'] for sol in sols})
            return f"Grandfathers of {person}: " + ", ".join(g.capitalize() for g in gfs) + "."

        # Who are the grandmothers of X?
        m = re.match(r"^Who are the grandmothers of ([A-Z][a-z]*)$", text)
        if m:
            (person,) = m.groups()
            p = norm(person)
            sols = list(self.prolog.query(f"grandmother(X,{p})"))
            if not sols:
                return f"No grandmothers of {person} found."
            gms = sorted({sol['X'] for sol in sols})
            return f"Grandmothers of {person}: " + ", ".join(g.capitalize() for g in gms) + "."

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
