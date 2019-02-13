#!/usr/bin/env python
"""Tools developed by OpenStreetCam to help contributors."""

import logging
import os
from argparse import ArgumentParser, RawTextHelpFormatter, SUPPRESS
from login_controller import LoginController
from osc_api_gateway import OSCAPIEnvironment
from osc_uploader import OSCUploadManager
from osc_utils import create_exif_from_metadata
from osc_discoverer import SequenceDiscovererFactory

LOGGER = logging.getLogger('osc_tools')
OSC_LOG_FILE = 'OSC_logs.log'


def main():
    """Entry point for the OSC scripts"""
    args = get_args()
    configure_log(args)
    # call the right sub command
    args.func(args)


def configure_login(args) -> LoginController:
    """Method to configure upload environment"""
    if args.env == 'p':
        LOGGER.debug("environment production")
        controller = LoginController(OSCAPIEnvironment.PRODUCTION)
    elif args.env == 't':
        LOGGER.debug("environment testing")
        controller = LoginController(OSCAPIEnvironment.TESTING)
    elif args.env == 's':
        LOGGER.debug("environment staging")
        controller = LoginController(OSCAPIEnvironment.STAGING)
    elif args.env == 'b':
        LOGGER.debug("environment beta")
        controller = LoginController(OSCAPIEnvironment.BETA)
    else:
        LOGGER.debug("environment default production")
        controller = LoginController(OSCAPIEnvironment.PRODUCTION)
    return controller


def configure_log(args):
    """Method to configure logging level"""
    LOGGER.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    file = logging.FileHandler(OSC_LOG_FILE)
    file.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)-35s: %(levelname)-8s %(message)s')
    file.setFormatter(formatter)

    # create console handler with a higher log level
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)

    if args.log_level == 'd':
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        LOGGER.debug("Debug logging selected")
    elif args.log_level == 'i':
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        console.setFormatter(formatter)
        LOGGER.debug("info logging selected")
    elif args.log_level == 'w':
        console.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(message)s')
        console.setFormatter(formatter)
        LOGGER.debug("Warning logging selected")

    # add the handlers to the logger
    LOGGER.addHandler(file)
    LOGGER.addHandler(console)


def upload_command(args):
    """Upload sequence from a given path"""
    path = args.path
    if not os.path.exists(path):
        LOGGER.warning("This is an invalid path.")
        return

    login_controller = configure_login(args)
    upload_manager = OSCUploadManager(login_controller)
    discoverers = SequenceDiscovererFactory.discoverers()
    finished_list = []
    LOGGER.warning("Searching for sequences...")
    for discoverer in discoverers:
        LOGGER.debug("Searching for %s", discoverer.name)
        sequences = discoverer.discover(path)
        if discoverer.ignored_for_upload:
            finished_list += sequences
            for sequence in sequences:
                LOGGER.warning("    Found sequence at path %s that is already uploaded at %s",
                               sequence.path,
                               login_controller.osc_api.sequence_link(sequence))
            continue
        for sequence in sequences:
            if sequence not in finished_list and \
                    sequence not in upload_manager.sequences:
                LOGGER.warning("    Found sequence at path %s. Sequence type %s.",
                               sequence.path,
                               discoverer.name)
                upload_manager.add_sequence_to_upload(sequence)
            else:
                LOGGER.debug("No sequence found for %s", discoverer.name)

    LOGGER.warning("Search completed.")
    if not upload_manager.sequences:
        if finished_list:
            LOGGER.warning("    No sequence to upload.")
        else:
            LOGGER.warning("    No sequence found.")
    else:
        LOGGER.warning("\n")
        upload_manager.start_upload()


def exif_generation_command(args):
    """Generate Exif from metadata"""
    path = args.path
    LOGGER.warning("Generating exif data from metadata file...")
    create_exif_from_metadata(path)
    LOGGER.warning("Finished.")


def get_args() -> list:
    """Method to create and configure a argument parser"""
    parser: ArgumentParser = ArgumentParser(prog='python osc_tools.py',
                                            formatter_class=RawTextHelpFormatter)

    subparsers = parser.add_subparsers(title='These are the available OSC commands',
                                       description='upload          Uploads sequences from a given'
                                                   ' path to OpenStreetCam\n'
                                                   'generate_exif   Generates Exif info for each '
                                                   'image from a metadata file',
                                       dest='sub command')
    subparsers.required = True
    create_parsers(subparsers)

    return parser.parse_args()


def _add_environment_argument(parser: ArgumentParser):
    parser.add_argument('-e',
                        '--env',
                        default='p',
                        required=False,
                        help=SUPPRESS,
                        choices=['p', 't', 's', 'b'])


def _add_logging_argument(parser: ArgumentParser):
    parser.add_argument('-l',
                        '--log_level',
                        required=False,
                        default='i',
                        help='Level of logging to console:\n'
                             '  d level (debug) will log every event to the console\n'
                             '  i level (info) will log every event more severe than '
                             'debug level to the console\n'
                             '  w level (warning) will log every event more severe than '
                             'info level to the console',
                        choices=['d', 'i', 'w'])


def create_parsers(subparsers: ArgumentParser):
    """Add all available parsers"""
    add_upload_parser(subparsers)
    add_generate_exif_parser(subparsers)


def add_upload_parser(subparsers: ArgumentParser):
    """Adds upload parser"""
    upload_parser = subparsers.add_parser('upload', formatter_class=RawTextHelpFormatter)
    upload_parser.set_defaults(func=upload_command)
    upload_parser.add_argument('-p',
                               '--path',
                               required=True,
                               help='Full path directory that contains sequence(s) '
                                    'folder(s) to upload')
    upload_parser.add_argument('-w',
                               '--workers',
                               required=False,
                               type=int,
                               default=10,
                               choices=range(1, 21),
                               metavar="[1-20]",
                               help='Number of parallel workers used to upload files. '
                                    'Default number is 10.')
    _add_environment_argument(upload_parser)
    _add_logging_argument(upload_parser)


def add_generate_exif_parser(subparsers: ArgumentParser):
    """Adds generate exif parser"""
    generate_parser = subparsers.add_parser('generate_exif', formatter_class=RawTextHelpFormatter)
    generate_parser.set_defaults(func=exif_generation_command)
    generate_parser.add_argument('-p',
                                 '--path',
                                 required=True,
                                 help='Folder PATH with OSC metadata file and images')
    _add_logging_argument(generate_parser)

    return subparsers


if __name__ == "__main__":
    main()
