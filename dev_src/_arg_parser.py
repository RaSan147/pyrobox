# add additional arguments to the parser

# the config must be imported from pyroboxCore
# from pyroboxCore import config

def main(config):
	config.parser.add_argument('--password', '-k',
							default=config.PASSWORD,
							type=str,
							help='Upload Password (default: %(default)s)')
	
	config.parser.add_argument('--no-upload', '-nu',
							action='store_true',
							default=False,
							help="Files can't be uploaded (default: %(default)s)")
	
	config.parser.add_argument('--no-zip', '-nz',
							action='store_true',
							default=False,
							help="Disable Folder->Zip downloading (default: %(default)s)")
	
	config.parser.add_argument('--no-update', '-no',
							action='store_true',
							default=False,
							help="Disable File Updating (ie: renaming, overwriting existing files) (On upload, if file exists, will add a number at the end(default: %(default)s)")
	
	config.parser.add_argument('--no-delete', '-nd',
							action='store_true',
							default=False,
							help="Disable File Deletion (default: %(default)s)")

	config.parser.add_argument('--no-download', '-ndw',
							action='store_true',
							default=False,
							help="Disable File Downloading [videos won't play either] (default: %(default)s)")
	
	config.parser.add_argument('--read-only', '-ro', 
							action='store_true',
							default=False,
							help='Read Only Mode *disables upload and any modifications ie: rename, delete* (default: %(default)s)')

	config.parser.add_argument('--view-only', '-vo',
							action='store_true',
							default=False,
							help="Only allowed to see file list, nothing else (default: %(default)s)")
	

	# config.parser.add_argument('--no-js', '-nj',
	# 						action='store_true',
	# 						default=False,
	# 						help="Disable Javascript in page(default: %(default)s)")
	