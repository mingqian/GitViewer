import getopt, sys, os
import subprocess
import StringIO

version = '0.1'

def usage():
    print('CLI tool for visualizing Git repo history')
    print('Verion %s written by Rafael Han (mq_han<at>hotmail.com)'  % version)
    print('-h, --help \t\t Get help info')
    print('-d, --dot=path \t\t Set path to Graphviz dot executable')
    print('-g, --git=path \t\t Set path to Git executable')
    print('-r, --repo=path \t Set path to repository root')
    print('-o, --output=file \t Set output filename')


def main():
    dot = ''
    git = ''
    repo = ''
    output = ''
    try:
        # Short option syntax: "hv:"
        # Long option syntax: "help" or "verbose="
        opts, args = getopt.getopt(sys.argv[1:], "hd:g:r:o:", ['help', 'dot=', 'git=', 'repo=', 'output='])

    except getopt.GetoptError, err:
        # Print debug info
        print str(err)
        sys.exit(0)

    for option, argument in opts:
        if option in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif option in ("-d", "--dot"):
            dot = argument
        elif option in ("-g", "--git"):
            git = argument
        elif option in ("-r", "--repo"):
            repo = argument
        elif option in ("-o", "--output"):
            output = argument

    if repo == '' or output == '':
        print('missing arguments. check by -h/--help')
        sys.exit(0)

    if not output.endswith('.pdf'):
        output += '.pdf'

    # find dot if not found
    if dot == '':
        dot = find_dot()
    if dot == '':
        print('dot not found. define by -d/--dot')
        sys.exit(0)

    # find git if not defined
    if git == '':
        git = find_git()
    if git == '':
        print('git not found. define by -g/--git')
        sys.exit(0)

    # test repo existence
    if not test_valid(repo):
        print('invalid repository.')
        sys.exit(0)


    generate(dot, git, repo, output)

def test_valid(path):
    if os.path.exists(path):
        return True
    else:
        return False

def generate(dot, git, repo, output):
    print('Getting git commit(s) ...')
    try:
        ret = subprocess.check_output([git, '--git-dir', repo+'/.git', 'log', '--all', '--pretty=format:"%h|%p|%d"'])
    except Exception as e:
        print str(e)
        sys.exit(0)

    decorated_lines = StringIO.StringIO(ret).readlines()
    print('processed %d commit(s) ...' % len(decorated_lines))

    decorated_dict = {}
    for decorated_line in decorated_lines:
        line = decorated_line.strip('"|\n').split('|')
        if len(line) == 3:
            decorated_dict[line[0]] = line[2]
    print('processed %d decorate(s) ...' % len(decorated_dict))


    print('Getting git ref branch(es) ...')
    try:
        ret = subprocess.check_output([git, '--git-dir', repo+'/.git', 'for-each-ref', '--format="%(objectname:short)|%(refname:short)"'])
    except Exception as e:
        print str(e)
        sys.exit(0)

    nodes = []

    ref_lines = StringIO.StringIO(ret).readlines()

    # add master branch history from old to new to nodes
    for ref_line in ref_lines:
        line = ref_line.strip('"|\n').split('|')
        if line[1].lower().startswith('master'):
            try:
                ret = subprocess.check_output([git, '--git-dir', repo+'/.git', 'log', '--reverse', '--first-parent', '--pretty=format:"%h"', line[0]])
            except Exception as e:
                print str(e)
                sys.exit(0)

            hash_lines = StringIO.StringIO(ret).readlines()
            tmp = []
            for hash_line in hash_lines:
                tmp.append(hash_line.strip('"|\n'))
            nodes.append(tmp)

    # add other branches history from old to new to nodes
    for ref_line in ref_lines:
        line = ref_line.strip('"|\n').split('|')
        if not line[1].lower().startswith('master'):
            try:
                ret = subprocess.check_output([git, '--git-dir', repo+'/.git', 'log', '--reverse', '--first-parent', '--pretty=format:"%h"', line[0]])
            except Exception as e:
                print str(e)
                sys.exit(0)

            tmp = []
            hash_lines = StringIO.StringIO(ret).readlines()
            for hash_line in hash_lines:
                tmp.append(hash_line.strip('"|\n'))
            nodes.append(tmp)


    print('Getting git merged branch(es) ...')
    try:
        ret = subprocess.check_output([git, '--git-dir', repo+'/.git', 'log', '--all', '--merges', '--pretty=format:"%h|%p"'])
    except Exception as e:
        print str(e)
        sys.exit(0)

    merged_lines = StringIO.StringIO(ret).readlines()

    for merged_line in merged_lines:
        merged_columns = (merged_line.strip('"|\n').split('|'))
        merged_parents = merged_columns[1].split(' ')
        if len(merged_parents) > 1:
            try:
                ret = subprocess.check_output([git, '--git-dir', repo+'/.git', 'log', '--reverse', '--first-parent', '--pretty=format:"%h"', merged_parents[1]])
            except Exception as e:
                print str(e)
                sys.exit(0)

            tmp = []
            hash_lines = StringIO.StringIO(ret).readlines()
            for hash_line in hash_lines:
                tmp.append(hash_line.strip('"|\n'))
            tmp.append(merged_columns[0])
            nodes.append(tmp)

    print('processed %d branch(es) ...' % len(nodes))

    print('Generating dot file ...')
    dot_string = 'strict digraph "tmp" {\n'

    # generating for nodes
    for i in range(len(nodes)):
        dot_string = dot_string + '  node[group="' + str(i+1) + '"];\n  '
        for j in range(len(nodes[i])):
            dot_string = dot_string + '"' + nodes[i][j] + '"'
            if j < len(nodes[i]) - 1:
                dot_string += ' -> '
            else:
                dot_string += ';'
        dot_string += '\n'

    decorate_count = 0
    for h, r in decorated_dict.items():
        dot_string = dot_string + '  subgraph Decorate' + str(decorate_count) + '\n  {\n'
        dot_string += '    rank="same";\n'
        dot_string = dot_string + '    "' + r.strip() + '" [shape="box", style="filled", fillcolor="#ddddff"];\n'
        dot_string = dot_string + '    "' + r.strip() + '" -> "' + h.strip() + '" [weight=0, arrowtype="none", dirtype="none", arrowhead="none", style="dotted"];\n'
        dot_string += '  }\n'
        decorate_count += 1

    dot_string += '}\n'


    try:
        with open('temp.dot', 'w') as f:
            f.write(dot_string)
    except Exception as e:
        print str(e)
        sys.exit(0)

    print('Generating version tree ...')
    try:
        subprocess.call([dot, 'temp.dot', '-Tpdf', '-Gsize=10,10', '-o', output])
    except Exception as e:
        print str(e)
        sys.exit(0)


    print('Done! ...')



if __name__ == "__main__":
    main()
