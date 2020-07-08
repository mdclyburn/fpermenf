import os
import re

# Cache lookups, etc.
RegexCache = {}

UserID = {}
GroupID = {}

def logChange(path, name, new):
    print(f"{path}: {name} -> {new}")

def fileType(path, t):
    if t == "regular":
        return os.path.isfile(path)
    elif t == "directory":
        return os.path.isdir(path)
    else:
        return False

def __getRegex(regex):
    if regex not in RegexCache.keys():
        RegexCache[regex] = re.compile(regex)
    return RegexCache[regex]

def fileName(path, regex):
    return __getRegex(regex).search(path) != None

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
