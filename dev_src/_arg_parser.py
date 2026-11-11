# add additional arguments to the parser
config = None
# the config must be imported from pyroboxCore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyroboxCore import Config

# Guest upload password default (None = generate random password at server start)
DEFAULT_UPLOAD_PASSWORD = None


def add_args(config:"Config"):
	if config._custom_cli_args_added:
		return
	config.parser.add_argument('--password', '-k',
							default=DEFAULT_UPLOAD_PASSWORD,
							type=str,
							help='[Value] Upload Password (default: randomly generated if not provided)',
							nargs="?",
							const=None)



	config.parser.add_argument('--qr', '-q',
							action='store_true',
							default=False,
							help='[Flag] Show QR code for easy access (default: %(default)s)[Requires pyqrcode]')



	config.parser.add_argument('--server-name', '-sn',
							type=str,
							default=None,
							help='[Value] In case you want to create a server User accounts based. --password must be always same and --admin-id and --admin-pass is required. See web doc for more info.'
								'[default: None]')

	config.parser.add_argument('--admin-id', '-aid',
							type=str,
							default=None,
							help='[Value] User name for admin id (In case you want to create a server User accounts based. --name and --admin-pass is required)'
								'[default: None]')

	config.parser.add_argument('--admin-pass', '-ak',
							type=str,
							default=None,
							help='[Value] Password for admin id (In case you want to create a User accounts based *named server*, --name and --admin-id is required)'
								'[default: None]')




	config.parser.add_argument('--no-signup', '-ns',
							action='store_true',
							default=False,
							help="[Flag] Disable signup page (default: %(default)s)")


	config.parser.add_argument('--guest-allowed', '-ga',
							action='store_true',
							default=True,
							help="[Flag] Allow guests to access server when USING Account based server (default: %(default)s)")

	config.parser.add_argument('--no-guest-allowed', '-ng',
							action='store_true',
							default=None,
							help="[Flag] Disallow guests to access server when USING Account/Admin based server (default: %(default)s)")

	config.parser.add_argument('--no-upload', '-nu',
							action='store_true',
							default=False,
							help="[Flag] Files can't be uploaded (default: %(default)s)")

	config.parser.add_argument('--no-zip', '-nz',
							action='store_true',
							default=False,
							help="[Flag] Disable Folder->Zip downloading (default: %(default)s)")

	config.parser.add_argument('--no-modify', '-nm',
							action='store_true',
							default=False,
							help="[Flag] Disable File Modification (ie: renaming, overwriting existing files) (On upload, if file exists, will add a number at the end(default: %(default)s)")

	config.parser.add_argument('--no-delete', '-nd',
							action='store_true',
							default=False,
							help="[Flag] Disable File Deletion (default: %(default)s)")

	config.parser.add_argument('--no-download', '-ndw',
							action='store_true',
							default=False,
							help="[Flag] Disable File Downloading [videos won't play either] (default: %(default)s)")

	config.parser.add_argument('--read-only', '-ro',
							action='store_true',
							default=False,
							help='[Flag] Read Only Mode *disables upload and any modifications ie: rename, delete* (default: %(default)s)')

	config.parser.add_argument('--view-only', '-vo',
							action='store_true',
							default=False,
							help="[Flag] Only allowed to see file list, nothing else (default: %(default)s)")

	config.parser.add_argument('--zip-limit', '-zl',
							default="6GB",
							type=str,
							help='[Value] Max size of zip file allowed to download (default: %(default)s) [can be bytes without suffix or suffixes like 1KB, 1MB, 1GB, 1TB]')

	config._custom_cli_args_added = True
