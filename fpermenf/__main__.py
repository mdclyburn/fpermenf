import argparse
import os
from os import path

from . import rules

def main():
    parser = argparse.ArgumentParser(description='Apply ownership/permissions to files.')
    parser.add_argument('-n', '--dry-run', help='do not actually apply actions',
                        action='store_true')
    parser.add_argument('directory', help='directory to descend from')
    args = parser.parse_args()
    walk(args.directory, args.dry_run)

def walk(root, dry_run=False):
    found_rules = {}
    for (dirpath, dirs, files) in os.walk(path.realpath(root)):
        statePath = path.join(dirpath, '.mdl-rules.json')
        if path.isfile(statePath):
            found_rules[dirpath] = rules.load(statePath)
            print(f"Found rules for '{dirpath}'.")
        if len(found_rules) == 0:
            continue

        applicableRulePaths = list(filter(
            lambda ruleDirpath: rules.applicable(ruleDirpath, dirpath),
            found_rules.keys()))
        applicableRulePaths.sort()

        applicableRules = []
        for rulePath in applicableRulePaths:
            applicableRules += found_rules[rulePath]

        paths = list(map(lambda file: path.join(dirpath, file), files))
        paths += list(map(lambda dir: path.join(dirpath, dir), dirs))
        rules.apply(applicableRules, paths, dry_run)

if __name__ == '__main__':
    main()
