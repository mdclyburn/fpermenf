import os

from . import attr

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

def __state_supported(name):
    return name in StateChecks.keys()

def load(path):
    import json
    with open(path) as rulesFile:
        rules = json.load(rulesFile)
    return [Rule(j['description'], j['match'], j['state']) for j in rules]

def applicable(stateFileDir, dirToCheck):
    # The path's rules should be used if removing the state file's file name
    # from the path yields a path that is the same as what
    # os.path.commonpath(stateFilePathWithoutFile, currentFilePath) returns.
    return os.path.commonprefix([stateFileDir, dirToCheck]) == stateFileDir


def merge_state(rules):
    merged_state = {}
    for r in rules:
        merged_state.update(r.state)

    return merged_state

def apply(rules, paths, dry_run):
    for path in paths:
        states = merge_state([r for r in rules if r.matches(path)])

        # Apply states to the file as necessary.
        header_printed = False
        for state_name in states.keys():
            if not __state_supported(state_name):
                print(f"  {state_name}: warning: not recognized")
                continue
            state_matches = (StateChecks[state_name])(path, states[state_name])
            if not state_matches and not header_printed:
                print(f"{path}:")
                header_printed = True

            if not state_matches and not dry_run:
                (StateApply[state_name])(path, states[state_name])
            elif not state_matches and dry_run:
                print(f"  {state_name}: {states[state_name]}")
