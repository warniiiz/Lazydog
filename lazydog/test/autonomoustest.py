#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


# main
def main():
    
    print(1)
    print(None == 0)
    print(os.path.basename('/folder/file.ext'))
    print(os.path.splitext('/folder/file.ext')[0])
    print(os.path.splitext(os.path.basename('/folder/file.ext.ext2'))[0])
    print(os.path.splitext(os.path.basename('/folder/file/'))[0])
    print(os.path.basename('/folder/file/'))

    l = ['1', '22', 'aaaa', '666666', '333']
    print(l)
    print(sorted(l))
    print(sorted(l, key = len))
    l.sort(lambda x: -len(x))
    print(l)

if __name__ == "__main__":
    main()