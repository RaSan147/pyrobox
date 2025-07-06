import os
import subprocess
import re

import shutil

from UX_Tools import get_exe_location, make_dir, xpath

FFMPEG = get_exe_location("ffmpeg")


__ffmpeg_subtitle_formats = (
    "srt",   # SubRip
    "vtt",   # WebVTT
    "ass",   # Advanced SubStation Alpha
    "ssa",   # SubStation Alpha
    "sub",   # MicroDVD
    "smi",   # SAMI
    "mpl",   # MPL2
    "txt",   # VPlayer
    "idx",   # VobSub (DVD)
    "sup"    # PGS (Blu-ray)
)

def extract_subtitles_from_file(input_file, output_format="vtt", output_dir=None, default_output_name_prefix=''):
	"""
	Extracts subtitles from a video file and saves them in the specified format.
	* input_file: The path to the input video file.
	* output_format: The output format for the subtitles. Default is `vtt`.
	* output_dir: The directory to save the output files. If `None`, the output files will be saved in the same directory as the input file.
	* default_output_name_prefix: The prefix to use for the output file names. If `None`, the input file name will be used as the prefix.
	* returns: A list of tuples containing the subtitle name and the path to the output file.
	"""
	output_paths = []
	sub_names = []

	file_name = os.path.splitext(os.path.basename(input_file))[0]

	if not output_dir:
		output_dir = os.path.dirname(input_file)
	make_dir(output_dir)

	input_dir = os.path.dirname(os.path.abspath(input_file))

	if not os.path.isfile(input_file):
		raise FileNotFoundError(f"The file '{input_file}' does not exist.")

	if not FFMPEG:
		# we don't want to raise an exception here, just return an empty list
		return []

	try:
		# check for str or vtt file startswith same name, if vtt, add, if str, convert to vtt and add
		for file in os.scandir(input_dir):
			if file.is_dir() or not file.name.startswith(file_name) or not file.name.endswith(__ffmpeg_subtitle_formats):
				continue

			srt_name = file.name[len(file_name):][:-4]
			if not srt_name:
				srt_name = 'sub'
				# remove all non-alphanumeric characters
				srt_name = re.sub(r'[<>:"/\\|?*]', '_', srt_name)

				while srt_name in sub_names:
					srt_name += "_" + str(len(sub_names) + 1)

			if default_output_name_prefix:
				srt_path = f"{default_output_name_prefix}_{srt_name}.{output_format}"
			else:
				srt_path = f"{file_name}_{srt_name}.{output_format}"

			srt_path = xpath(output_dir, srt_path)


			if not file_name.endswith(output_format):
				# convert srt to vtt
				subprocess.run(
					[FFMPEG, "-i", file.path, '-y', srt_path],
					check=True
				)

			else:
				shutil.copy(file.path, srt_path)

			output_paths.append((srt_name, srt_path))
		
		# Run ffmpeg to analyze the file
		process = subprocess.run(
			[FFMPEG, "-i", input_file],
			stderr=subprocess.PIPE,
			stdout=subprocess.PIPE,
			text=True
		)
		output = process.stderr  # ffmpeg logs info in stderr

		# Extract stream information (Subtitle streams)
		# Example: Stream #0:1(eng): Subtitle: dvd_subtitle
		stream_pattern = re.compile(
			r"Stream #(\d+:\d+)((?:\(\w+\))?): Subtitle: (.+)"
		)
		n = 1
		for match in stream_pattern.finditer(output):
			stream_index, sub_name, codec = match.groups()
			if sub_name:
				if sub_name.startswith('(') and sub_name.endswith(')'):
					sub_name = sub_name[1:-1]
					if sub_name in sub_names:
						sub_name = f"{sub_name}_{n}"
			else:
				sub_name = f"subtitle_{n}"

			sub_names.append(sub_name)
			n += 1

			# Generate output filename
			if default_output_name_prefix:
				output_filename = f"{default_output_name_prefix}_{sub_name}.{output_format}"
			else:
				output_filename = f"{file_name}_{sub_name}.{output_format}"

			# remove any invalid characters from the filename
			output_filename = re.sub(r'[<>:"/\\|?*]', '_', output_filename)

			output_filename = xpath(output_dir, output_filename)

			make_dir(output_dir) # Create the output directory if it doesn't exist

			# Generate output path
			output_paths.append((sub_name, output_filename))

			# Use ffmpeg to extract the audio stream
			subprocess.run(
				[FFMPEG, "-i", input_file, "-map", stream_index, '-y', output_filename],
				check=True
			)

		return output_paths

	except subprocess.CalledProcessError as e:
		raise RuntimeError(f"Error processing file {input_file}: {e}")
	except Exception as e:
		raise RuntimeError(f"Unexpected error: {e}")

# Example Usage
if __name__ == "__main__":
	input_file = "te-st/videos/Candle.mp4"
	try:
		output_files = extract_subtitles_from_file(input_file)
		print("Extracted subtitles:")
		for path in output_files:
			print(path)
	except Exception as e:
		print(f"Error: {e}")
