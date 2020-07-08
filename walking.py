#!/usr/bin/env python

import os
from os import path
import re

MatchChecks = {
    "file_type": (lambda path, req: fileType(path, req)),
    "name": (lambda path, req: fileName(path, req))
}

StateChecks = {
    "owner": (lambda path, req: isOwner(path, req)),
    "group": (lambda path, req: isGroup(path, req)),
    "mode": (lambda path, req: isPermission(path, req))
}

StateApply = {
    "owner": (lambda path, req: setOwner(path, req)),
    "group": (lambda path, req: setGroup(path, req)),
    "mode": (lambda path, req: setPermission(path, req))
}

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

def walk(root):
    rules = {}
    for (dirpath, dirs, files) in os.walk(path.realpath(root)):
        statePath = path.join(dirpath, '.mdl-rules.json')
        if path.isfile(statePath):
            rules[dirpath] = loadRules(statePath)
            print(f"Found rules for '{dirpath}'.")
        if len(rules) == 0:
            continue

        applicableRulePaths = list(filter(
            lambda ruleDirpath: statesApplicable(ruleDirpath, dirpath),
            rules.keys()))
        applicableRulePaths.sort()

        applicableRules = []
        for rulePath in applicableRulePaths:
            applicableRules += rules[rulePath]

        paths = list(map(lambda file: path.join(dirpath, file), files))
        paths += list(map(lambda dir: path.join(dirpath, dir), dirs))
        apply(applicableRules, paths)

def loadRules(path):
    import json
    with open(path) as rulesFile:
        rules = json.load(rulesFile)
    return list(map(lambda j: Rule(j['description'], j['match'], j['state']), rules))

def statesApplicable(stateFileDir, dirToCheck):
    # The path's rules should be used if removing the state file's file name
    # from the path yields a path that is the same as what
    # os.path.commonpath(stateFilePathWithoutFile, currentFilePath) returns.
    return path.commonprefix([stateFileDir, dirToCheck]) == stateFileDir

def apply(rules, paths):
    for path in paths:
        # Merge the states to get what the state of the file should be.
        states = {}
        for rule in rules:
            if rule.matches(path):
                for k in rule.state.keys():
                    states[k] = rule.state[k]

        # Apply states to the file as necessary.
        for state in states.keys():
            if state not in StateChecks.keys():
                continue
            if not (StateChecks[state])(path, states[state]):
                (StateApply[state])(path, states[state])

def logChange(path, name, new):
    print(f"{path}: {name} -> {new}")

def fileType(path, t):
    if t == "regular":
        return os.path.isfile(path)
    elif t == "directory":
        return os.path.isdir(path)
    else:
        return False

RegexCache = {}
def __getRegex(regex):
    if regex not in RegexCache.keys():
        RegexCache[regex] = re.compile(regex)
    return RegexCache[regex]

def fileName(path, regex):
    return __getRegex(regex).search(path) != None

# Need to translate names to numbers without consulting the system
# thousands of times, so cache lookups here.
UserID = {}
GroupID = {}

def __lookupOwner(o):
    if o not in UserID.keys():
        import pwd
        UserID[o] = pwd.getpwnam(o).pw_uid
    return UserID[o]

def __lookupGroup(g):
    if g not in GroupID.keys():
        import pwd
        GroupID[g] = pwd.getpwnam(g).pw_uid
    return GroupID[g]

def isOwner(path, o):
    owner = os.stat(path).st_uid
    return owner == __lookupOwner(o)

def setOwner(path, o):
    uid = __lookupOwner(o)
    os.chown(path, uid, -1)
    logChange(path, 'owner', uid)

def isGroup(path, g):
    group = os.stat(path).st_gid
    return group == __lookupGroup(g)

def setGroup(path, g):
    gid = __lookupGroup(g)
    os.chown(path, -1, gid)
    logChange(path, 'group', gid)

def isPermission(path, mode):
    if len(mode) != 3 and len(mode) != 4:
        raise Exception(f'Unsupported mode {mode}')

    currentMode = oct(os.stat(path).st_mode)
    shouldBe = currentMode[:-len(mode)] + mode
    return currentMode == shouldBe

def setPermission(path, mode):
    currentMode = oct(os.stat(path).st_mode)
    shouldBe = currentMode[:-len(mode)] + mode
    dec = int(shouldBe, 8)
    os.chmod(path, dec)
    logChange(path, 'mode', dec)
