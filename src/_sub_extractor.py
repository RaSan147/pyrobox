import os
import subprocess
import re

import shutil

from .tools import get_exe_location

FFMPEG = get_exe_location("ffmpeg")

def extract_subtitles_from_file(input_file, output_format="vtt", output_dir=None, default_output_name_prefix=None):
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

	if not os.path.isfile(input_file):
		raise FileNotFoundError(f"The file '{input_file}' does not exist.")

	if not FFMPEG:
		# we don't want to raise an exception here, just return an empty list
		return []

	try:
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
				file_name = os.path.splitext(os.path.basename(input_file))[0]
				output_filename = f"{file_name}_{sub_name}.{output_format}"

			# remove any invalid characters from the filename
			output_filename = re.sub(r'[<>:"/\\|?*]', '', output_filename)

			if output_dir:
				output_filename = os.path.join(output_dir, output_filename)

			else:
				# Use the same directory as the input file
				output_dir = os.path.dirname(input_file)
				output_filename = os.path.join(output_dir, output_filename)

			os.makedirs(output_dir, exist_ok=True) # Create the output directory if it doesn't exist

			output_filename = f"{os.path.splitext(input_file)[0]}_{sub_name}.{output_format}"

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
