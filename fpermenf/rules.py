import os

import attr

class Rule:
    def __init__(self, description, match={}, state={}):
        self.description = description
        self.match = match
        self.state = state

    def matches(self, path):
        if len(self.match) == 0:
            return True

        for criteria in self.match.keys():
            if criteria not in MatchChecks.keys():
                raise Exception(f"'{criteria}' is not a valid match option.")
            if not (MatchChecks[criteria])(path, self.match[criteria]):
                return False
            return True

MatchChecks = {
    "file_type": (lambda path, req: attr.fileType(path, req)),
    "name": (lambda path, req: attr.fileName(path, req))
}

StateChecks = {
    "owner": (lambda path, req: attr.isOwner(path, req)),
    "group": (lambda path, req: attr.isGroup(path, req)),
    "mode": (lambda path, req: attr.isPermission(path, req))
}

StateApply = {
    "owner": (lambda path, req: attr.setOwner(path, req)),
    "group": (lambda path, req: attr.setGroup(path, req)),
    "mode": (lambda path, req: attr.setPermission(path, req))
}

def load(path):
    import json
    with open(path) as rulesFile:
        rules = json.load(rulesFile)
    return list(map(lambda j: Rule(j['description'], j['match'], j['state']), rules))

def applicable(stateFileDir, dirToCheck):
    # The path's rules should be used if removing the state file's file name
    # from the path yields a path that is the same as what
    # os.path.commonpath(stateFilePathWithoutFile, currentFilePath) returns.
    return os.path.commonprefix([stateFileDir, dirToCheck]) == stateFileDir

def apply(rules, paths, dry_run):
    for path in paths:
        # Merge the states to get what the state of the file should be.
        states = {}
        for rule in rules:
            if rule.matches(path):
                for k in rule.state.keys():
                    states[k] = rule.state[k]

        # Apply states to the file as necessary.
        header_printed = False
        for state in states.keys():
            if state not in StateChecks.keys():
                continue
            state_matches = (StateChecks[state])(path, states[state])
            if not state_matches and not header_printed:
                print(f"{path}:")
                header_printed = True

            if not state_matches and not dry_run:
                pass
                # (StateApply[state])(path, states[state])
            elif not state_matches and dry_run:
                print(f"  {state}: {states[state]}")
