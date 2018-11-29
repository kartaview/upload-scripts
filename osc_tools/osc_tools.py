#!/usr/bin/python
"""This script is used to upload the files from the specified path to OSC servers."""

import argparse
from argparse import ArgumentParser


def main():
    """Entry point for the script"""
    args = get_args()
    configure_log(args)
    path = args.path
    print(path)
    configure_upload_env(args)


def configure_upload_env(args):
    """Method to configure upload environment"""
    if args.env == 'p':
        print("environment production")
    if args.env == 't':
        print("environment testing")
    if args.env == 's':
        print("environment staging")


def configure_log(args):
    """Method to configure logging level"""
    if args.log_level == 'i':
        print('info logging')
    elif args.log_level == 'd':
        print('debugging logs')
    elif args.log_level == 'w':
        print('warnings logs')
    elif args.log_level == 'si':
        print('save info to file and console')
    elif args.log_level == 'sd':
        print('save debug to file and console')
    elif args.log_level == 'sw':
        print('save warnings to file and console')


def get_args():
    """Method to create and configure a argument parser"""
    parser: ArgumentParser = argparse.ArgumentParser(prog='upload',
                                                     description='This script will upload all the '
                                                                 'files form the path sent as '
                                                                 'argument.')
    parser.add_argument('-p',
                        '--path',
                        required=True,
                        help='Full path directory that contains photos')
    parser.add_argument('-l',
                        '--log_level',
                        required=False,
                        default='i',
                        help='Specify level of logging to console.'
                             'd level will log everything to the console'
                             'w level will log only warnings to console'
                             'i level will log only events to console'
                             'sd Debug level will log everything to file and console'
                             'sw Warnings level will log only warnings to file and console'
                             'si Info level will log only events to file and console',
                        choices=['i', 'w', 'd', 'si', 'sw', 'sd'])
    parser.add_argument('-e',
                        '--env',
                        default='p',
                        required=False,
                        help='Specify the environment on which to upload.'
                             'p for Production'
                             't for testing'
                             's for staging',
                        choices=['p', 't', 's'])

    return parser.parse_args()


if __name__ == "__main__":
    main()
