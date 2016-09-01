import getopt, sys

version = '0.1'

def usage():
    print('CLI tool for visualizing Git repo history')
    print(('Verion %s written by Rafael Han (mq_han<at>hotmail.com)')  % version)
    print('-h, --help \t\t Get help info')
    print('-o, --output=file \t Set output file')
    print('-d, --dir=directory \t Set repo root dir')
def main():
    try:
        # Short option syntax: "hv:"
        # Long option syntax: "help" or "verbose="
        opts, args = getopt.getopt(sys.argv[1:], "ho:d:", ['help', 'output=', 'dir='])

    except getopt.GetoptError, err:
        # Print debug info
        print str(err)
        sys.exit(0)

    for option, argument in opts:
        if option in ("-h", "--help"):
            usage()
        elif option in ("-v", "--output"):
            output = argument
        elif option in ("-d", "--dir"):
            gitdir = argument

if __name__ == "__main__":
    main()
